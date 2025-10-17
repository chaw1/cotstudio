# MinerU国内部署解决方案

## 问题诊断

错误信息显示:
```
failed to fetch anonymous token: Get "https://auth.docker.io/token?..."
dial tcp 199.96.63.75:443: connectex: A connection attempt failed
```

**根本原因**: 无法连接到Docker Hub (docker.io),这是国内网络环境的常见问题。

## 解决方案

### 方案1: 使用国内镜像源Dockerfile (推荐)

已创建 `docker/mineru/Dockerfile.cn`,使用阿里云镜像源。

#### 1.1 修改docker-compose.yml

```yaml
services:
  mineru:
    build:
      context: ./docker/mineru
      dockerfile: Dockerfile.cn  # 使用国内优化版本
    # ... 其他配置保持不变
```

#### 1.2 重新构建

```powershell
docker-compose build mineru
docker-compose up -d
```

### 方案2: 配置Docker镜像加速器

#### 2.1 配置阿里云镜像加速

1. 打开Docker Desktop
2. 进入 Settings → Docker Engine
3. 添加以下配置:

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://mirror.ccs.tencentyun.com"
  ],
  "insecure-registries": [],
  "experimental": false
}
```

4. 点击 "Apply & Restart"

#### 2.2 重新拉取镜像

```powershell
docker-compose build --no-cache mineru
docker-compose up -d
```

### 方案3: 手动拉取NVIDIA镜像

#### 3.1 使用阿里云镜像

```powershell
# 从阿里云拉取CUDA镜像
docker pull registry.cn-hangzhou.aliyuncs.com/acs/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 重新标记为原始名称
docker tag registry.cn-hangzhou.aliyuncs.com/acs/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 构建MinerU镜像
docker-compose build mineru
docker-compose up -d
```

### 方案4: 使用HTTP代理 (如果有VPN)

#### 4.1 配置Docker代理

Docker Desktop → Settings → Resources → Proxies

```
HTTP Proxy: http://127.0.0.1:7890
HTTPS Proxy: http://127.0.0.1:7890
```

#### 4.2 重新构建

```powershell
docker-compose build mineru
docker-compose up -d
```

### 方案5: 离线部署 (最稳定)

如果网络问题持续,可以使用离线部署:

#### 5.1 在有网络的机器上保存镜像

```bash
# 构建并保存镜像
docker-compose build mineru
docker save -o mineru-image.tar cotstudio-mineru:latest

# 传输到目标服务器
```

#### 5.2 在目标服务器上加载镜像

```powershell
docker load -i mineru-image.tar
docker-compose up -d
```

## 推荐步骤

**对于国内用户,推荐使用方案1+方案2组合:**

### 第一步: 配置Docker镜像加速

```powershell
# 1. 打开Docker Desktop设置
# 2. Docker Engine添加镜像源
# 3. 重启Docker
```

### 第二步: 修改docker-compose.yml

```powershell
cd E:\Chris\Document\OneDrive\Project\cotstudio
```

在 `docker-compose.yml` 中找到 mineru 服务,修改:

```yaml
services:
  mineru:
    build:
      context: ./docker/mineru
      dockerfile: Dockerfile.cn  # 改用国内版本
```

### 第三步: 清理并重新构建

```powershell
# 清理旧的构建缓存
docker-compose down
docker builder prune -f

# 重新构建(使用国内镜像)
docker-compose build --no-cache mineru

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f mineru
```

## 验证部署

```powershell
# 检查容器状态
docker-compose ps

# 查看MinerU日志
docker-compose logs mineru

# 测试健康检查
curl http://localhost:8001/health

# 如果curl不可用,用PowerShell
Invoke-WebRequest -Uri http://localhost:8001/health
```

## 常见问题

### Q1: 仍然无法连接Docker Hub
**A**: 使用方案1的 `Dockerfile.cn`,它使用阿里云镜像,不依赖Docker Hub

### Q2: 构建过程中pip下载超时
**A**: `Dockerfile.cn` 已配置阿里云pip镜像,如仍有问题可尝试:
```dockerfile
RUN pip3 config set global.timeout 300
```

### Q3: PyTorch下载失败
**A**: 使用清华镜像:
```bash
pip3 install torch==2.5.1 --index-url https://pypi.tuna.tsinghua.edu.cn/simple/
```

### Q4: 显示"no matching manifest for windows/amd64"
**A**: 确保Docker Desktop启用了WSL2或Hyper-V,并在设置中启用了Linux容器模式

## 镜像源参考

### Docker镜像源
- 阿里云: `https://registry.cn-hangzhou.aliyuncs.com`
- 中科大: `https://docker.mirrors.ustc.edu.cn`
- 腾讯云: `https://mirror.ccs.tencentyun.com`
- 网易: `https://hub-mirror.c.163.com`

### Python镜像源
- 阿里云: `https://mirrors.aliyun.com/pypi/simple/`
- 清华: `https://pypi.tuna.tsinghua.edu.cn/simple/`
- 豆瓣: `https://pypi.douban.com/simple/`

### PyTorch镜像源
- 清华: `https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cu121/`
- 阿里云: `https://mirrors.aliyun.com/pytorch-wheels/cu121/`

## 下一步

部署成功后,继续以下步骤:

1. **模型下载**: 首次启动会自动下载8-12GB模型
2. **配置系统**: 在Web界面配置MinerU引擎
3. **测试OCR**: 上传PDF测试OCR功能
4. **性能优化**: 根据实际情况调整batch_size

如有问题,查看日志:
```powershell
docker-compose logs -f mineru
```
