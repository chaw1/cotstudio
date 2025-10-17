# Docker Desktop 代理配置指南

## 问题
虽然PowerShell设置了代理环境变量,但Docker Desktop并未使用这些代理设置。

## 解决方案: 在Docker Desktop中配置代理

### 步骤1: 打开Docker Desktop设置

1. 打开 **Docker Desktop**
2. 点击右上角的 **⚙️ 设置图标**
3. 选择 **Resources** → **Proxies**

### 步骤2: 配置代理设置

在代理设置页面,启用 **Manual proxy configuration** 并填入:

```
HTTP Proxy:  http://127.0.0.1:10808
HTTPS Proxy: http://127.0.0.1:10808
```

如果有不需要代理的地址,在 **Bypass** 字段添加:
```
localhost,127.0.0.1,*.local
```

### 步骤3: 应用并重启

1. 点击 **Apply & Restart**
2. 等待 Docker Desktop 重启完成(约30秒)

### 步骤4: 验证代理生效

在PowerShell中运行:

```powershell
# 测试能否拉取镜像
docker pull hello-world

# 如果成功,继续构建MinerU
cd E:\Chris\Document\OneDrive\Project\cotstudio
docker-compose build mineru
```

## 图形界面位置

```
Docker Desktop
    └── Settings (⚙️)
         └── Resources
              └── Proxies
                   ├── ☑ Manual proxy configuration
                   ├── HTTP Proxy:  http://127.0.0.1:10808
                   ├── HTTPS Proxy: http://127.0.0.1:10808
                   └── Bypass: localhost,127.0.0.1
```

## 完整构建流程

配置好代理后:

```powershell
# 1. 清理旧的构建
docker-compose down

# 2. 测试代理(可选)
docker pull hello-world

# 3. 构建MinerU服务
docker-compose build mineru

# 4. 启动所有服务
docker-compose up -d

# 5. 查看MinerU日志
docker-compose logs -f mineru
```

## 常见问题

### Q: 我的代理端口不是10808怎么办?

A: 根据你的实际代理端口修改,常见端口:
- Clash: 7890
- V2Ray: 10808, 1080
- SSR: 1080, 10800

### Q: 配置后仍然无法连接?

A: 检查以下几点:
1. 代理软件是否正在运行
2. 代理软件是否允许来自局域网的连接
3. 防火墙是否阻止了连接
4. 尝试重启Docker Desktop

### Q: 不想用代理,有其他方法吗?

A: 可以使用已创建的国内镜像版本:

修改 `docker-compose.yml`:
```yaml
services:
  mineru:
    build:
      context: ./docker/mineru
      dockerfile: Dockerfile.cn  # 使用国内优化版本
```

然后:
```powershell
docker-compose build mineru
```

## 验证成功

成功的构建输出应该包含:

```
[+] Building 120.5s (18/18) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
 => [1/12] FROM docker.io/nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
 ...
 => exporting to image
 => => writing image sha256:...
 => => naming to docker.io/library/cotstudio-mineru
```

## 下一步

构建成功后:

```powershell
# 启动所有服务
docker-compose up -d

# 等待MinerU初始化(首次需下载模型,10-30分钟)
docker-compose logs -f mineru

# 测试健康检查
Invoke-WebRequest -Uri http://localhost:8001/health
```
