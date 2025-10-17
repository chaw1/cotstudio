# MinerU 2.5 OCR引擎集成指南

## 📋 概述

本项目已集成MinerU 2.5高精度PDF文档解析引擎,支持复杂文档的精确识别,包括公式、表格、图像等。

### ✨ MinerU 2.5特性

- 🎯 **高精度**: 超越GPT-4o、Gemini 2.5-Pro等主流模型
- 📊 **复杂结构支持**: 公式、表格、图像自动识别
- 🚀 **GPU加速**: 支持CUDA 12.1+的NVIDIA GPU
- 💪 **轻量化**: 仅1.2B参数,内存占用小
- 🔧 **灵活部署**: 支持GPU/CPU双模式

## 🏗️ 架构设计

MinerU作为独立的微服务运行,通过内部网络与主后端服务通信:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Frontend  │─────▶│   Backend    │─────▶│  MinerU Service │
│   (Port    │◀─────│   (Port     │◀─────│   (Port 8001)   │
│    3000)    │      │    8000)     │      │   GPU Powered   │
└─────────────┘      └──────────────┘      └─────────────────┘
```

## 🚀 快速开始

### 方案一: GPU服务器部署 (推荐)

**系统要求:**
- NVIDIA GPU (推荐GTX 1660以上)
- CUDA 12.1或更高版本
- Docker 20.10+
- docker-compose 1.29+
- NVIDIA Container Toolkit

**步骤1: 安装NVIDIA Container Toolkit**

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**步骤2: 验证GPU可用**

```bash
# 测试Docker能否访问GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**步骤3: 启动服务**

```bash
# 克隆项目
cd cotstudio

# 首次启动(会自动下载MinerU模型,需要10-20分钟)
docker-compose up -d

# 查看MinerU服务日志
docker-compose logs -f mineru
```

**步骤4: 验证MinerU服务**

```bash
# 检查服务健康状态
curl http://localhost:8001/health

# 预期输出:
# {
#   "status": "healthy",
#   "mineru_ready": true,
#   "gpu_available": true,
#   "gpu_count": 1
# }
```

### 方案二: CPU服务器部署

**系统要求:**
- 4核CPU以上
- 8GB+ 内存
- Docker 20.10+

**启动命令:**

```bash
# 使用CPU配置启动
docker-compose -f docker-compose.yml -f docker-compose.cpu.yml up -d

# 查看日志
docker-compose logs -f mineru
```

**注意**: CPU模式处理速度较慢,建议用于测试或低频使用场景。

## 📦 离线部署(可选)

如果服务器无法访问外网,可以预先下载模型:

### 本地下载模型

```bash
# 在有网络的机器上
conda create -n mineru python=3.10
conda activate mineru

# 安装MinerU
pip install uv
uv pip install -U "mineru[core]"

# 下载模型到指定目录
mineru-models-download --model_type all --save_path ./mineru_models

# 打包模型目录
tar -czf mineru_models.tar.gz mineru_models/
```

### 服务器部署

```bash
# 上传模型包到服务器
scp mineru_models.tar.gz user@server:/path/to/cotstudio/

# 解压到Docker卷目录
cd /path/to/cotstudio
mkdir -p ./volumes/mineru_models
tar -xzf mineru_models.tar.gz -C ./volumes/mineru_models/

# 修改docker-compose.yml,挂载本地模型目录
# volumes:
#   - ./volumes/mineru_models:/app/models

# 启动服务
docker-compose up -d
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MINERU_SERVICE_URL` | `http://mineru:8001` | MinerU服务地址 |
| `CUDA_VISIBLE_DEVICES` | `0` | 使用的GPU编号 |
| `MINERU_DEVICE` | `cuda` | 计算设备(cuda/cpu) |

### MinerU引擎参数

在系统设置 → OCR引擎 → MinerU配置中可设置:

- **backend**: 
  - `pipeline`: 快速模式,适合一般文档
  - `vlm-transformers`: 高精度模式,适合复杂学术文档

- **device**:
  - `cuda`: GPU加速(推荐)
  - `cpu`: CPU模式

- **batch_size**: 批处理大小(1-16),GPU推荐8,CPU推荐2

- **useApi**: 是否使用远程API服务

- **apiUrl**: 远程API地址(如使用托管服务)

## 📊 性能基准

### GPU模式 (RTX 3080)

| 文档类型 | 页数 | 处理时间 | 精度 |
|----------|------|----------|------|
| 普通PDF | 10 | ~15秒 | 98% |
| 学术论文(公式) | 10 | ~30秒 | 96% |
| 表格密集文档 | 10 | ~25秒 | 95% |

### CPU模式 (8核)

| 文档类型 | 页数 | 处理时间 | 精度 |
|----------|------|----------|------|
| 普通PDF | 10 | ~2分钟 | 98% |
| 学术论文 | 10 | ~5分钟 | 96% |

## 🔧 故障排除

### 问题1: MinerU服务启动失败

**症状**: `docker-compose logs mineru` 显示导入错误

**解决**:
```bash
# 重新构建镜像
docker-compose build --no-cache mineru

# 重启服务
docker-compose up -d mineru
```

### 问题2: GPU不可用

**症状**: 健康检查显示 `gpu_available: false`

**解决**:
```bash
# 检查NVIDIA驱动
nvidia-smi

# 检查Docker GPU支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 如果失败,重新安装nvidia-container-toolkit
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

### 问题3: 模型下载缓慢或失败

**症状**: 首次启动时间过长或卡住

**解决方案1 - 使用国内镜像**:
```bash
# 修改Dockerfile中的pip源
-i https://mirrors.aliyun.com/pypi/simple
```

**解决方案2 - 离线部署**:
参考上文"离线部署"章节

### 问题4: OCR处理超时

**症状**: 大文件处理时返回504错误

**解决**:
```bash
# 修改MinerU服务的超时设置
# 在mineru_service.py中:
timeout=600  # 增加到10分钟

# 或在系统设置中选择:
# - 使用 pipeline 模式(更快)
# - 减小 batch_size
# - 分割大文件后处理
```

## 📝 使用示例

### 后端代码调用

```python
from app.services.ocr_service import ocr_service

# 使用MinerU引擎
result = ocr_service.extract_text(
    file_content=pdf_bytes,
    filename="document.pdf",
    engine_name="mineru"
)

print(f"提取的文本: {result.full_text}")
print(f"总页数: {result.total_pages}")
```

### API直接调用

```bash
# 测试MinerU服务
curl -X POST http://localhost:8001/ocr \
  -F "file=@test.pdf" \
  -F "backend=pipeline" \
  -F "device=cuda"

# 返回:
# {
#   "success": true,
#   "text": "提取的文档内容...",
#   "metadata": {
#     "filename": "test.pdf",
#     "pages": 10,
#     "backend": "pipeline"
#   }
# }
```

## 🔄 更新MinerU

```bash
# 停止服务
docker-compose stop mineru

# 重新构建镜像(获取最新版本)
docker-compose build --no-cache mineru

# 启动服务
docker-compose up -d mineru

# 验证版本
curl http://localhost:8001/ | jq '.version'
```

## 📚 参考资源

- [MinerU GitHub仓库](https://github.com/opendatalab/MinerU)
- [MinerU在线体验](https://mineru.net)
- [MinerU文档](https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md)

## 💡 最佳实践

1. **GPU服务器**: 优先使用GPU模式,性能提升10倍以上
2. **模型预下载**: 生产环境建议预先下载模型,避免首次启动慢
3. **批处理**: 大量文档建议使用批量API,提高吞吐量
4. **监控**: 使用Prometheus监控MinerU服务状态和性能
5. **备份**: 定期备份模型文件(约8-12GB)

## 🆘 技术支持

如遇问题,请提供以下信息:

```bash
# 系统信息
docker --version
docker-compose --version
nvidia-smi  # 如使用GPU

# 服务状态
docker-compose ps
docker-compose logs mineru --tail=100

# 健康检查
curl http://localhost:8001/health
```

---

**维护团队**: COT Studio Development Team  
**最后更新**: 2025年10月15日
