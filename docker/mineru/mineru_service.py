"""
MinerU 2.5 OCR 微服务
提供高精度的PDF文档解析服务
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化FastAPI应用
app = FastAPI(
    title="MinerU 2.5 OCR Service",
    description="高精度PDF文档解析服务",
    version="2.5.0"
)

# 全局变量存储MinerU实例
mineru_instance = None


class OCRRequest(BaseModel):
    """OCR请求模型"""
    backend: str = "pipeline"  # pipeline 或 vlm-transformers
    device: str = "cuda"  # cuda 或 cpu
    batch_size: int = 8
    output_format: str = "markdown"  # markdown, json, text


class OCRResponse(BaseModel):
    """OCR响应模型"""
    success: bool
    text: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


def init_mineru():
    """初始化MinerU引擎"""
    global mineru_instance
    
    try:
        logger.info("正在初始化MinerU引擎...")
        
        # 检查是否有GPU
        import torch
        has_gpu = torch.cuda.is_available()
        logger.info(f"GPU可用: {has_gpu}")
        
        if has_gpu:
            logger.info(f"GPU设备: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        # 这里不需要显式初始化MinerU对象
        # MinerU通过命令行工具使用，我们将直接调用
        mineru_instance = True
        
        logger.info("✓ MinerU引擎初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"✗ MinerU引擎初始化失败: {e}")
        mineru_instance = None
        return False


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("========================================")
    logger.info("MinerU 2.5 OCR Service 启动中...")
    logger.info("========================================")
    
    # 初始化MinerU
    if not init_mineru():
        logger.warning("MinerU初始化失败，服务将以降级模式运行")
    
    logger.info("服务已就绪，等待请求...")


@app.get("/")
async def root():
    """根路径 - 服务状态"""
    return {
        "service": "MinerU 2.5 OCR Service",
        "version": "2.5.0",
        "status": "running",
        "gpu_available": mineru_instance is not None
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    import torch
    
    return {
        "status": "healthy",
        "mineru_ready": mineru_instance is not None,
        "gpu_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
    }


@app.post("/ocr", response_model=OCRResponse)
async def process_ocr(
    file: UploadFile = File(...),
    backend: str = "pipeline",
    device: str = "cuda",
    batch_size: int = 8
):
    """
    处理OCR请求
    
    Args:
        file: 上传的PDF或图像文件
        backend: 处理后端 (pipeline: 快速模式, vlm-transformers: 高精度模式)
        device: 计算设备 (cuda: GPU, cpu: CPU)
        batch_size: 批处理大小
    
    Returns:
        OCRResponse: 包含提取的文本和元数据
    """
    
    if not mineru_instance:
        raise HTTPException(
            status_code=503,
            detail="MinerU引擎未就绪"
        )
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="mineru_")
    input_path = None
    output_dir = None
    
    try:
        # 保存上传的文件
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.pdf', '.png', '.jpg', '.jpeg']:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        input_path = Path(temp_dir) / file.filename
        with open(input_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"处理文件: {file.filename} ({len(content)} bytes)")
        
        # 创建输出目录
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 构建MinerU命令
        import subprocess
        
        cmd = [
            "mineru",
            "-p", str(input_path),
            "-o", str(output_dir),
            "--backend", backend,
            "--device", device,
            "--source", "modelscope"  # 使用ModelScope国内镜像源
        ]
        
        if backend == "pipeline":
            cmd.extend(["--batch-size", str(batch_size)])
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info(f"工作目录: {temp_dir}")
        logger.info(f"输入文件存在: {input_path.exists()}, 大小: {input_path.stat().st_size if input_path.exists() else 0}")
        
        # 执行MinerU - 增加超时到30分钟,OCR模型处理大文件需要时间
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时,给OCR模型足够的处理时间
            )
            logger.info(f"✓ MinerU命令执行完成")
        except subprocess.TimeoutExpired as e:
            logger.error(f"✗ MinerU命令超时(1800秒)")
            raise HTTPException(
                status_code=504,
                detail="OCR处理超时(30分钟),请尝试使用更小的文件"
            )
        except Exception as e:
            logger.error(f"✗ MinerU命令执行异常: {type(e).__name__}: {str(e)}")
            raise
        
        # 记录命令输出用于调试
        logger.info(f"MinerU return code: {result.returncode}")
        if result.stdout:
            logger.info(f"MinerU stdout: {result.stdout[:2000]}")
        if result.stderr:
            # 记录完整的stderr以查看所有错误信息
            logger.warning(f"MinerU stderr (完整): {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"MinerU执行失败(return code={result.returncode}): {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"OCR处理失败: {result.stderr}"
            )
        
        # 列出输出目录的所有内容用于调试
        logger.info(f"输出目录: {output_dir}")
        try:
            all_files = list(output_dir.rglob("*"))
            logger.info(f"输出目录中共有 {len(all_files)} 个文件/目录")
            for f in all_files[:30]:  # 只显示前30个
                logger.info(f"  - {f.relative_to(output_dir)} ({'dir' if f.is_dir() else f'file {f.stat().st_size}B'})")
        except Exception as e:
            logger.error(f"列出输出目录失败: {e}")
        
        # 尝试多种可能的输出路径
        # MinerU 2.5可能的输出格式:
        # 1. output/<filename_stem>/<filename_stem>.md
        # 2. output/<filename_stem>.md
        # 3. output/auto/<filename_stem>.md
        
        possible_paths = [
            output_dir / Path(file.filename).stem / f"{Path(file.filename).stem}.md",  # 标准路径
            output_dir / f"{Path(file.filename).stem}.md",  # 直接在output下
            output_dir / "auto" / f"{Path(file.filename).stem}.md",  # auto子目录
        ]
        
        markdown_file = None
        for path in possible_paths:
            logger.info(f"检查路径: {path}")
            if path.exists():
                markdown_file = path
                logger.info(f"✓ 找到输出文件: {markdown_file}")
                break
        
        if not markdown_file:
            # 最后尝试: 搜索任何markdown文件
            markdown_files = list(output_dir.rglob("*.md"))
            logger.info(f"搜索到的所有.md文件: {markdown_files}")
            if markdown_files:
                markdown_file = markdown_files[0]
                logger.info(f"使用找到的markdown文件: {markdown_file}")
            else:
                logger.error(f"未找到任何markdown文件")
                raise HTTPException(
                    status_code=500,
                    detail="未找到OCR输出结果"
                )
        
        # 读取提取的文本
        with open(markdown_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        
        # 收集元数据
        metadata = {
            "filename": file.filename,
            "backend": backend,
            "device": device,
            "file_size": len(content),
            "output_format": "markdown",
            "pages": extracted_text.count("---") + 1  # 粗略估计页数
        }
        
        logger.info(f"✓ OCR处理完成: {file.filename}")
        
        return OCRResponse(
            success=True,
            text=extracted_text,
            metadata=metadata
        )
    
    except HTTPException:
        # HTTPException直接向上传递,不要再包装
        raise
    
    except Exception as e:
        logger.error(f"OCR处理异常: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"OCR处理失败: {type(e).__name__}: {str(e)}"
        )
    
    finally:
        # 清理临时文件
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")


@app.post("/ocr/batch")
async def process_batch_ocr(
    files: list[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    批量处理OCR请求
    """
    if not mineru_instance:
        raise HTTPException(
            status_code=503,
            detail="MinerU引擎未就绪"
        )
    
    results = []
    
    for file in files:
        try:
            response = await process_ocr(file)
            results.append({
                "filename": file.filename,
                "success": True,
                "text_length": len(response.text)
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


if __name__ == "__main__":
    # 启动服务
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"启动MinerU OCR服务: http://{host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
