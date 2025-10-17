# MinerU 部署网络问题快速修复

## 问题原因
无法连接到 Docker Hub (docker.io) 拉取 NVIDIA CUDA 镜像,这是国内网络环境的常见问题。

## 已完成的修复

### ✅ 1. 创建国内优化版 Dockerfile
- 文件: `docker/mineru/Dockerfile.cn`
- 使用阿里云 CUDA 镜像源
- 配置阿里云 pip 和 PyTorch 镜像

### ✅ 2. 修改 docker-compose.yml
已将 mineru 服务改为使用 `Dockerfile.cn`

## 立即执行

### 方式A: 快速重试(推荐)

```powershell
# 1. 确保在项目根目录
cd E:\Chris\Document\OneDrive\Project\cotstudio

# 2. 清理旧的构建缓存
docker-compose down
docker builder prune -f

# 3. 重新构建 MinerU 服务(使用国内镜像)
docker-compose build --no-cache mineru

# 4. 启动所有服务
docker-compose up -d

# 5. 查看 MinerU 日志
docker-compose logs -f mineru
```

### 方式B: 先配置 Docker 镜像加速(更稳定)

#### 第一步: 配置 Docker Desktop

1. 打开 Docker Desktop
2. 点击右上角设置图标 ⚙️
3. 选择 **Docker Engine**
4. 在编辑器中添加或修改以下配置:

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
```

5. 点击 **Apply & Restart**
6. 等待 Docker 重启完成

#### 第二步: 重新构建

```powershell
# 清理并重新构建
docker-compose down
docker builder prune -f
docker-compose build mineru
docker-compose up -d

# 查看日志
docker-compose logs -f mineru
```

## 验证部署

### 1. 检查容器状态

```powershell
docker-compose ps
```

应该看到 mineru 服务状态为 `Up`

### 2. 查看 MinerU 日志

```powershell
docker-compose logs mineru
```

成功启动应该看到:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 3. 测试健康检查

```powershell
# PowerShell 测试
Invoke-WebRequest -Uri http://localhost:8001/health

# 或使用 curl (如果已安装)
curl http://localhost:8001/health
```

应该返回:
```json
{
  "status": "healthy",
  "service": "MinerU",
  "version": "2.5.0",
  "gpu_available": true,
  "gpu_count": 1
}
```

## 常见问题排查

### 问题1: 构建时仍然连接不上

**症状**: 
```
failed to fetch anonymous token
```

**解决**:
1. 确认已使用 `Dockerfile.cn`
2. 检查 docker-compose.yml 中 mineru 服务的 dockerfile 配置
3. 确认 `Dockerfile.cn` 文件存在于 `docker/mineru/` 目录

```powershell
# 验证文件是否存在
Test-Path .\docker\mineru\Dockerfile.cn
```

### 问题2: pip 安装超时

**症状**:
```
ReadTimeoutError: HTTPSConnectionPool
```

**解决**:
等待重试,阿里云镜像源通常很稳定。如果持续失败,可以尝试清华源:

编辑 `docker/mineru/Dockerfile.cn`,将:
```dockerfile
https://mirrors.aliyun.com/pypi/simple/
```

改为:
```dockerfile
https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 问题3: GPU 不可用

**症状**:
```
"gpu_available": false
```

**解决**:
1. 检查 NVIDIA 驱动安装
```powershell
nvidia-smi
```

2. 如果没有 GPU 或不需要 GPU,使用 CPU 模式:
```powershell
docker-compose -f docker-compose.yml -f docker-compose.cpu.yml up -d
```

### 问题4: 模型下载慢

**首次启动**: MinerU 会自动下载 8-12GB 模型,可能需要 10-30 分钟

**查看下载进度**:
```powershell
docker-compose logs -f mineru
```

**加速方法**: 如果本地 Anaconda 已有模型,可以挂载本地目录:

编辑 `docker-compose.yml`:
```yaml
volumes:
  - E:/path/to/your/mineru_models:/app/models  # 改为你的本地路径
  - mineru_temp:/app/temp
  - mineru_output:/app/output
```

## 完整重启流程

如果遇到任何问题,可以完整重启:

```powershell
# 1. 停止所有服务
docker-compose down

# 2. 清理 MinerU 容器和镜像
docker rmi cotstudio-mineru:latest

# 3. 清理构建缓存
docker builder prune -f

# 4. 重新构建(无缓存)
docker-compose build --no-cache mineru

# 5. 启动服务
docker-compose up -d

# 6. 实时查看日志
docker-compose logs -f mineru
```

## 下一步

部署成功后:

1. **等待模型下载完成** (首次启动约 10-30 分钟)
2. **在系统设置中配置 MinerU 引擎**
3. **上传测试 PDF 验证 OCR 功能**

## 获取帮助

如果问题仍未解决,请提供以下信息:

```powershell
# 1. Docker 版本
docker --version
docker-compose --version

# 2. 系统信息
systeminfo | findstr /C:"OS"

# 3. GPU 信息 (如果有)
nvidia-smi

# 4. 完整错误日志
docker-compose logs mineru > mineru_error.log
```
