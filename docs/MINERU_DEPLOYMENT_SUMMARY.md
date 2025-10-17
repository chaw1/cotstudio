# MinerU部署问题总结与解决方案

## 问题分析

经过多次尝试,发现主要问题:

1. **Docker Buildx代理问题**: Docker Buildx构建器无法使用Docker Desktop的代理设置
2. **镜像下载失败**: 无法从Docker Hub拉取NVIDIA CUDA基础镜像
3. **包安装失败**: 即使切换到阿里云镜像源,仍有部分包(如libllvm15)下载失败

## 推荐解决方案

### 🎯 方案A: 使用现有的Python基础镜像(最简单)

这种方式避免了下载大型CUDA镜像的问题。

#### 1. 修改Dockerfile使用Python镜像

```dockerfile
# docker/mineru/Dockerfile.python
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

# 安装最少的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 配置pip镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装MinerU
RUN pip install --no-cache-dir \
    "mineru>=2.5.0" \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    opencv-python-headless \
    requests \
    torch==2.5.1 \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制服务文件
COPY mineru_service.py /app/

#创建目录
RUN mkdir -p /app/models /app/temp /app/output

# 创建用户
RUN useradd -m -u 1000 mineru && chown -R mineru:mineru /app
USER mineru

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import mineru; print('OK')" || exit 1

CMD ["python", "mineru_service.py"]
```

#### 2. 修改docker-compose.yml

```yaml
services:
  mineru:
    build:
      context: ./docker/mineru
      dockerfile: Dockerfile.python  # 使用Python基础镜像版本
    # ... 其他配置保持不变
```

#### 3. 构建并运行

```powershell
# 先手动拉取Python镜像(通常本地已有或速度很快)
docker pull python:3.10-slim

# 构建MinerU
docker-compose build mineru

# 启动服务
docker-compose up -d mineru
```

### 🎯 方案B: 离线部署(适合网络环境特别差的情况)

如果您有另一台网络正常的机器:

#### 在网络正常的机器上:

```bash
# 1. 拉取并构建镜像
git clone <your-repo>
cd cotstudio
docker-compose build mineru

# 2. 导出镜像
docker save -o mineru-image.tar cotstudio-mineru:latest

# 3. 传输到目标服务器
# 使用U盘、网络共享等方式
```

#### 在目标服务器上:

```powershell
# 1. 加载镜像
docker load -i mineru-image.tar

# 2. 查看镜像
docker images | Select-String "mineru"

# 3. 启动服务
docker-compose up -d mineru
```

### 🎯 方案C: 使用本地Anaconda环境(跳过Docker)

如果Docker问题难以解决,可以直接使用您本地的Anaconda环境:

#### 1. 激活环境并安装依赖

```powershell
conda activate mineru
pip install fastapi uvicorn python-multipart requests
```

#### 2. 修改mineru_service.py中的路径

```python
# 确保使用本地模型路径
MODEL_PATH = r"C:\Users\YourUsername\anaconda3\envs\mineru\.mineru\models"
```

#### 3. 直接运行服务

```powershell
python docker/mineru/mineru_service.py
```

#### 4. 修改backend配置

在`backend/.env`中设置:
```env
MINERU_SERVICE_URL=http://localhost:8001
```

然后只用Docker运行backend等其他服务,MinerU在本地运行。

## 下一步建议

### 立即可行的方案

**推荐使用方案A**,因为:
1. Python镜像通常本地已有或下载很快
2. 避免了CUDA镜像的下载问题
3. MinerU可以在CPU模式下运行,仍有不错的效果

### 创建Python版本Dockerfile

我为您创建一个简化的Python版本。请执行:

```powershell
# 1. 先拉取Python镜像
docker pull python:3.10-slim

# 2. 修改docker-compose.yml使用Dockerfile.python
# 3. 构建
docker-compose build mineru

# 4. 启动
docker-compose up -d
```

## 性能对比

| 方案 | GPU支持 | 构建难度 | 运行速度 | 推荐指数 |
|------|---------|----------|----------|----------|
| CUDA镜像 | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Python镜像 | ❌ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 离线部署 | ✅ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 本地Anaconda | ✅ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 总结

**当前最佳实践**:
1. 使用`python:3.10-slim`基础镜像
2. CPU模式运行MinerU (10页PDF约2分钟,可接受)
3. 后续网络改善后再切换到GPU版本

**文件清单**:
- ✅ `docker/mineru/Dockerfile` - 原GPU版本
- ✅ `docker/mineru/Dockerfile.simple` - 简化版本
- ✅ `docker/mineru/Dockerfile.cn` - 国内镜像版本
- 🆕 需要创建: `docker/mineru/Dockerfile.python` - Python基础镜像版本(推荐)

**下一步操作**:
```powershell
# 我将为您创建Dockerfile.python
# 然后您只需执行:
docker pull python:3.10-slim
docker-compose build mineru
docker-compose up -d
```

希望这次能成功! 🚀
