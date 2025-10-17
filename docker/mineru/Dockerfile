# MinerU 2.5 OCR Service Dockerfile
# 支持GPU加速的PDF文档解析服务

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    CUDA_HOME=/usr/local/cuda \
    PATH="/usr/local/cuda/bin:${PATH}" \
    LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    wget \
    curl \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 创建符号链接
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/python3.10 /usr/bin/python3

# 升级pip并安装uv (快速包管理器)
RUN python -m pip install --upgrade pip && \
    pip install uv

# 安装MinerU及其依赖
RUN uv pip install --system -U "mineru[core]" -i https://mirrors.aliyun.com/pypi/simple

# 安装PyTorch GPU版本 (CUDA 12.1)
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    torchvision==0.20.1 \
    torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121

# 安装额外的Python依赖
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pillow \
    numpy \
    opencv-python-headless

# 创建模型和数据目录
RUN mkdir -p /app/models /app/temp /app/output

# 复制模型下载脚本
COPY scripts/download_mineru_models.sh /app/scripts/
RUN chmod +x /app/scripts/download_mineru_models.sh

# 复制MinerU服务代码
COPY mineru_service.py /app/
COPY config.yaml /app/

# 创建非root用户
RUN useradd --create-home --shell /bin/bash mineru && \
    chown -R mineru:mineru /app

USER mineru

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import mineru; print('MinerU OK')" || exit 1

# 暴露服务端口
EXPOSE 8001

# 启动命令
CMD ["python", "mineru_service.py"]
