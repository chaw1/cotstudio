"""
OCR服务 - 支持多个OCR引擎
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from io import BytesIO
import json
import re
from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2)
    page_number: int = 1


@dataclass
class DocumentStructure:
    """文档结构信息"""
    total_pages: int
    page_results: List[List[OCRResult]]
    full_text: str
    text_blocks: List[Dict[str, Any]]


class BaseOCREngine(ABC):
    """OCR引擎基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def extract_text(self, file_content: bytes, filename: str) -> DocumentStructure:
        """
        从文件中提取文本
        
        Args:
            file_content: 文件内容
            filename: 文件名
            
        Returns:
            DocumentStructure: 文档结构和文本内容
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查OCR引擎是否可用"""
        pass


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR引擎实现"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._ocr = None
        self._init_engine()
    
    def _init_engine(self):
        """初始化PaddleOCR引擎"""
        try:
            # 延迟导入以避免启动时的依赖问题
            from paddleocr import PaddleOCR
            
            # 配置PaddleOCR参数
            ocr_config = {
                'use_angle_cls': True,
                'lang': self.config.get('lang', 'ch'),
                'use_gpu': self.config.get('use_gpu', False),
                'show_log': False
            }
            
            self._ocr = PaddleOCR(**ocr_config)
            logger.info("PaddleOCR engine initialized successfully")
            
        except ImportError:
            logger.warning("PaddleOCR not available - install with: pip install paddlepaddle paddleocr")
            self._ocr = None
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self._ocr = None
    
    def is_available(self) -> bool:
        """检查PaddleOCR是否可用"""
        return self._ocr is not None
    
    def extract_text(self, file_content: bytes, filename: str) -> DocumentStructure:
        """使用PaddleOCR提取文本"""
        if not self.is_available():
            raise FileProcessingError("PaddleOCR engine not available", "OCR_ENGINE_UNAVAILABLE")
        
        try:
            # 处理不同文件类型
            if filename.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_content)
            else:
                return self._extract_from_image(file_content)
                
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            raise FileProcessingError(f"OCR processing failed: {str(e)}", "OCR_PROCESSING_FAILED")
    
    def _extract_from_pdf(self, file_content: bytes) -> DocumentStructure:
        """从PDF文件提取文本"""
        try:
            # 使用pdf2image转换PDF为图片
            from pdf2image import convert_from_bytes
            
            images = convert_from_bytes(file_content)
            page_results = []
            text_blocks = []
            full_text_parts = []
            
            for page_num, image in enumerate(images, 1):
                # 将PIL图像转换为numpy数组
                import numpy as np
                img_array = np.array(image)
                
                # 使用PaddleOCR处理图像
                result = self._ocr.ocr(img_array, cls=True)
                
                page_ocr_results = []
                page_text_parts = []
                
                if result and result[0]:
                    for line in result[0]:
                        if len(line) >= 2:
                            bbox = line[0]
                            text_info = line[1]
                            
                            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                text = text_info[0]
                                confidence = text_info[1]
                            else:
                                text = str(text_info)
                                confidence = 0.9
                            
                            if text and text.strip():
                                # 计算边界框
                                x_coords = [point[0] for point in bbox]
                                y_coords = [point[1] for point in bbox]
                                x1, y1 = min(x_coords), min(y_coords)
                                x2, y2 = max(x_coords), max(y_coords)
                                
                                ocr_result = OCRResult(
                                    text=text.strip(),
                                    confidence=confidence,
                                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                                    page_number=page_num
                                )
                                page_ocr_results.append(ocr_result)
                                page_text_parts.append(text.strip())
                                
                                # 添加到文本块
                                text_blocks.append({
                                    'text': text.strip(),
                                    'page': page_num,
                                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                    'confidence': confidence,
                                    'type': 'text'
                                })
                
                page_results.append(page_ocr_results)
                if page_text_parts:
                    full_text_parts.append('\n'.join(page_text_parts))
            
            full_text = '\n\n'.join(full_text_parts)
            
            return DocumentStructure(
                total_pages=len(images),
                page_results=page_results,
                full_text=full_text,
                text_blocks=text_blocks
            )
            
        except ImportError:
            logger.warning("pdf2image not available - install with: pip install pdf2image")
            raise FileProcessingError("PDF processing not available", "PDF_PROCESSOR_UNAVAILABLE")
        except Exception as e:
            logger.error(f"PDF OCR processing failed: {e}")
            raise FileProcessingError(f"PDF OCR failed: {str(e)}", "PDF_OCR_FAILED")
    
    def _extract_from_image(self, file_content: bytes) -> DocumentStructure:
        """从图像文件提取文本"""
        try:
            from PIL import Image
            import numpy as np
            
            # 加载图像
            image = Image.open(BytesIO(file_content))
            img_array = np.array(image)
            
            # 使用PaddleOCR处理
            result = self._ocr.ocr(img_array, cls=True)
            
            ocr_results = []
            text_blocks = []
            text_parts = []
            
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        bbox = line[0]
                        text_info = line[1]
                        
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = text_info[1]
                        else:
                            text = str(text_info)
                            confidence = 0.9
                        
                        if text and text.strip():
                            # 计算边界框
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            x1, y1 = min(x_coords), min(y_coords)
                            x2, y2 = max(x_coords), max(y_coords)
                            
                            ocr_result = OCRResult(
                                text=text.strip(),
                                confidence=confidence,
                                bbox=(int(x1), int(y1), int(x2), int(y2)),
                                page_number=1
                            )
                            ocr_results.append(ocr_result)
                            text_parts.append(text.strip())
                            
                            # 添加到文本块
                            text_blocks.append({
                                'text': text.strip(),
                                'page': 1,
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                'confidence': confidence,
                                'type': 'text'
                            })
            
            full_text = '\n'.join(text_parts)
            
            return DocumentStructure(
                total_pages=1,
                page_results=[ocr_results],
                full_text=full_text,
                text_blocks=text_blocks
            )
            
        except Exception as e:
            logger.error(f"Image OCR processing failed: {e}")
            raise FileProcessingError(f"Image OCR failed: {str(e)}", "IMAGE_OCR_FAILED")


class MinerUEngine(BaseOCREngine):
    """MinerU 2.5引擎实现 - 高精度PDF文档解析"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._service_url = None
        self._init_engine()
    
    def _init_engine(self):
        """初始化MinerU引擎连接"""
        try:
            # MinerU作为独立微服务运行
            import os
            self._service_url = os.getenv('MINERU_SERVICE_URL', 'http://mineru:8001')
            logger.info(f"MinerU service URL: {self._service_url}")
            
            # 检查服务是否可用
            import requests
            response = requests.get(f"{self._service_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("MinerU engine initialized successfully")
            else:
                logger.warning(f"MinerU service responded with status {response.status_code}")
                self._service_url = None
                
        except Exception as e:
            logger.warning(f"MinerU service not available: {e}")
            self._service_url = None
    
    def is_available(self) -> bool:
        """检查MinerU服务是否可用"""
        if not self._service_url:
            return False
        
        try:
            import requests
            response = requests.get(f"{self._service_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def extract_text(self, file_content: bytes, filename: str) -> DocumentStructure:
        """使用MinerU提取文本"""
        if not self._service_url:
            raise FileProcessingError("MinerU service not available", "MINERU_UNAVAILABLE")
        
        try:
            import requests
            from io import BytesIO
            
            # 准备文件上传
            files = {
                'file': (filename, BytesIO(file_content), 'application/octet-stream')
            }
            
            # 配置参数
            backend = self.config.get('backend', 'pipeline')  # pipeline或vlm-transformers
            device = self.config.get('device', 'cuda')
            
            # 调用MinerU服务
            response = requests.post(
                f"{self._service_url}/ocr",
                files=files,
                params={
                    'backend': backend,
                    'device': device,
                    'batch_size': self.config.get('batch_size', 8)
                },
                timeout=300  # 5分钟超时
            )
            
            if response.status_code != 200:
                raise FileProcessingError(
                    f"MinerU service error: {response.text}",
                    "MINERU_ERROR"
                )
            
            result = response.json()
            
            if not result.get('success'):
                raise FileProcessingError(
                    result.get('error', 'Unknown error'),
                    "MINERU_PROCESSING_ERROR"
                )
            
            # 解析MinerU返回的结果
            extracted_text = result.get('text', '')
            metadata = result.get('metadata', {})
            
            # 按页分割文本 (基于markdown的页分隔符)
            pages = extracted_text.split('---\n\n')
            page_results = []
            text_blocks = []
            
            for page_num, page_text in enumerate(pages, 1):
                if page_text.strip():
                    ocr_result = OCRResult(
                        text=page_text.strip(),
                        confidence=0.95,  # MinerU高精度
                        bbox=None,
                        page_number=page_num
                    )
                    page_results.append([ocr_result])
                    
                    text_blocks.append({
                        'text': page_text.strip(),
                        'page': page_num,
                        'bbox': None,
                        'confidence': 0.95,
                        'type': 'markdown'
                    })
            
            return DocumentStructure(
                total_pages=len(pages),
                page_results=page_results,
                full_text=extracted_text,
                text_blocks=text_blocks
            )
            
        except requests.exceptions.Timeout:
            logger.error("MinerU service timeout")
            raise FileProcessingError("MinerU processing timeout", "MINERU_TIMEOUT")
        except Exception as e:
            logger.error(f"MinerU processing failed: {e}")
            raise FileProcessingError(f"MinerU failed: {str(e)}", "MINERU_FAILED")


class FallbackOCREngine(BaseOCREngine):
    """回退OCR引擎 - 用于纯文本文件"""
    
    def is_available(self) -> bool:
        """回退引擎总是可用"""
        return True
    
    def extract_text(self, file_content: bytes, filename: str) -> DocumentStructure:
        """从纯文本文件提取内容"""
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            text = None
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                # 如果所有编码都失败，使用错误处理
                text = file_content.decode('utf-8', errors='replace')
            
            # 创建简单的文本块
            text_blocks = [{
                'text': text,
                'page': 1,
                'bbox': None,
                'confidence': 1.0,
                'type': 'text'
            }]
            
            # 创建OCR结果
            ocr_result = OCRResult(
                text=text,
                confidence=1.0,
                bbox=None,
                page_number=1
            )
            
            return DocumentStructure(
                total_pages=1,
                page_results=[[ocr_result]],
                full_text=text,
                text_blocks=text_blocks
            )
            
        except Exception as e:
            logger.error(f"Fallback text extraction failed: {e}")
            raise FileProcessingError(f"Text extraction failed: {str(e)}", "TEXT_EXTRACTION_FAILED")


class OCRService:
    """OCR服务管理器"""
    
    def __init__(self):
        self.engines = {}
        self._init_engines()
    
    def _init_engines(self):
        """初始化所有OCR引擎"""
        # 初始化PaddleOCR引擎
        paddle_engine = PaddleOCREngine()
        if paddle_engine.is_available():
            self.engines['paddleocr'] = paddle_engine
            logger.info("PaddleOCR engine registered")
        
        # 初始化MinerU引擎
        mineru_engine = MinerUEngine()
        if mineru_engine.is_available():
            self.engines['mineru'] = mineru_engine
            logger.info("MinerU engine registered")
        
        # 初始化回退引擎
        self.engines['fallback'] = FallbackOCREngine()
        logger.info("Fallback OCR engine registered")
    
    def get_available_engines(self) -> List[str]:
        """获取可用的OCR引擎列表"""
        return [name for name, engine in self.engines.items() if engine.is_available()]
    
    def get_engine(self, engine_name: str) -> Optional[BaseOCREngine]:
        """获取指定的OCR引擎"""
        return self.engines.get(engine_name)
    
    def extract_text(self, file_content: bytes, filename: str, engine_name: str = 'paddleocr', engine_config: Dict[str, Any] = None) -> DocumentStructure:
        """
        使用指定引擎提取文本
        
        Args:
            file_content: 文件内容
            filename: 文件名
            engine_name: OCR引擎名称
            engine_config: 引擎配置参数
            
        Returns:
            DocumentStructure: 提取的文档结构
        """
        engine_config = engine_config or {}
        
        # 根据文件类型选择合适的引擎
        if filename.lower().endswith(('.txt', '.md', '.json', '.tex', '.latex')):
            engine_name = 'fallback'
        
        engine = self.get_engine(engine_name)
        if not engine:
            # 如果指定引擎不可用，尝试使用回退引擎
            logger.warning(f"Engine {engine_name} not available, using fallback")
            engine = self.get_engine('fallback')
        
        if not engine:
            raise FileProcessingError("No OCR engine available", "NO_OCR_ENGINE")
        
        # 如果是MinerU引擎，应用配置
        if engine_name == 'mineru' and hasattr(engine, 'config'):
            engine.config.update(engine_config)
            logger.info(f"Using OCR engine: {engine.name} with config: {engine_config}")
        else:
            logger.info(f"Using OCR engine: {engine.name}")
        
        return engine.extract_text(file_content, filename)


# 创建全局OCR服务实例
ocr_service = OCRService()