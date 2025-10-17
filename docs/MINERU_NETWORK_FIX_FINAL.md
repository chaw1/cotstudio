# MinerU部署网络问题最终解决方案

## 问题根源

Docker Buildx (docker-compose使用的构建器) 不会自动继承Docker Desktop的代理设置。即使：
- ✅ PowerShell设置了HTTP_PROXY环境变量  
- ✅ Docker Desktop配置了Proxy设置
- ✅ 普通docker pull命令可以工作

**docker-compose build** 仍然无法连接到Docker Hub。

## 解决方案

### 方案1: 配置Buildx代理 (推荐)

#### 步骤1: 创建或编辑Docker配置文件

在Windows PowerShell中执行:

```powershell
# 创建.docker目录(如果不存在)
$dockerConfigPath = "$env:USERPROFILE\.docker"
if (!(Test-Path $dockerConfigPath)) {
    New-Item -ItemType Directory -Path $dockerConfigPath
}

# 编辑config.json
notepad "$dockerConfigPath\config.json"
```

#### 步骤2: 添加代理配置

在 `config.json` 中添加或修改:

```json
{
  "proxies": {
    "default": {
      "httpProxy": "http://127.0.0.1:10808",
      "httpsProxy": "http://127.0.0.1:10808",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
```

保存文件并关闭。

#### 步骤3: 重启Docker Desktop

```powershell
# 在Docker Desktop中点击重启,或者执行:
# 右键点击系统托盘的Docker图标 → Restart
```

#### 步骤4: 验证并构建

```powershell
cd E:\Chris\Document\OneDrive\Project\cotstudio

# 测试能否拉取镜像
docker pull hello-world

# 构建MinerU
docker-compose build mineru

# 启动服务
docker-compose up -d
```

### 方案2: 使用本地已有镜像 (如果有)

如果您本地已有Ubuntu或Python镜像:

```powershell
# 查看本地镜像
docker images

# 修改Dockerfile使用本地已有的镜像
# 例如将 FROM ubuntu:22.04 改为 FROM python:3.10-slim
```

### 方案3: 手动拉取所需镜像

```powershell
# 设置临时环境变量
$env:DOCKER_BUILDKIT=0

# 手动拉取基础镜像
docker pull ubuntu:22.04
docker pull python:3.10-slim

# 然后构建
docker-compose build mineru
```

### 方案4: 禁用BuildKit (最简单)

```powershell
# 禁用BuildKit使用传统构建器
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0

# 构建
docker-compose build mineru
```

## 完整修复流程 (推荐步骤)

### 第一步: 配置Buildx代理

```powershell
# 1. 编辑Docker配置
notepad $env:USERPROFILE\.docker\config.json

# 2. 添加代理配置(见上方JSON示例)

# 3. 保存并重启Docker Desktop
```

### 第二步: 设置环境变量

```powershell
# 进入项目目录
cd E:\Chris\Document\OneDrive\Project\cotstudio

# 设置代理
$env:HTTP_PROXY = "http://127.0.0.1:10808"
$env:HTTPS_PROXY = "http://127.0.0.1:10808"

# 如果方案1不行,禁用BuildKit
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0
```

### 第三步: 执行构建

```powershell
# 清理旧构建
docker-compose down
docker system prune -f

# 构建MinerU
docker-compose build mineru

# 如果成功,启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f mineru
```

## 验证配置是否生效

### 测试1: Docker配置

```powershell
# 查看Docker配置
Get-Content $env:USERPROFILE\.docker\config.json

# 应该看到proxies配置
```

### 测试2: 拉取测试镜像

```powershell
# 测试能否通过代理拉取镜像
docker pull hello-world

# 如果成功,说明代理配置正确
```

### 测试3: BuildKit状态

```powershell
# 查看BuildKit是否被禁用
echo "DOCKER_BUILDKIT: $env:DOCKER_BUILDKIT"
echo "COMPOSE_DOCKER_CLI_BUILD: $env:COMPOSE_DOCKER_CLI_BUILD"

# 如果输出是0,说明已禁用BuildKit
```

## 常见问题

### Q1: config.json文件不存在
**A**: 运行以下命令创建:
```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.docker" -Force
echo '{"proxies":{"default":{"httpProxy":"http://127.0.0.1:10808","httpsProxy":"http://127.0.0.1:10808"}}}' > "$env:USERPROFILE\.docker\config.json"
```

### Q2: 配置后仍然无法连接
**A**: 尝试禁用BuildKit:
```powershell
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0
docker-compose build mineru
```

### Q3: 代理端口不是10808
**A**: 修改为您实际的代理端口:
- Clash: 通常是 7890
- V2Ray: 通常是 10808 或 1080
- 查看代理软件的设置确认端口

### Q4: 完全无法连接网络
**A**: 考虑使用离线部署:
1. 在有网络的环境构建镜像
2. 导出镜像: `docker save -o mineru.tar cotstudio-mineru`
3. 传输到目标服务器
4. 加载镜像: `docker load -i mineru.tar`

## 推荐的完整命令序列

```powershell
# === 第一部分: 配置 ===

# 1. 创建Docker配置文件
$configPath = "$env:USERPROFILE\.docker\config.json"
$configContent = @"
{
  "proxies": {
    "default": {
      "httpProxy": "http://127.0.0.1:10808",
      "httpsProxy": "http://127.0.0.1:10808",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
"@
$configContent | Out-File -FilePath $configPath -Encoding UTF8

# 2. 重启Docker Desktop (手动操作)
Write-Host "请重启Docker Desktop,然后按任意键继续..." -ForegroundColor Yellow
pause

# === 第二部分: 构建 ===

# 3. 进入项目目录
cd E:\Chris\Document\OneDrive\Project\cotstudio

# 4. 设置环境变量(双保险)
$env:HTTP_PROXY = "http://127.0.0.1:10808"
$env:HTTPS_PROXY = "http://127.0.0.1:10808"
$env:DOCKER_BUILDKIT=0  # 禁用BuildKit
$env:COMPOSE_DOCKER_CLI_BUILD=0

# 5. 测试连接
Write-Host "测试Docker网络连接..." -ForegroundColor Cyan
docker pull hello-world

# 6. 构建MinerU
Write-Host "开始构建MinerU服务..." -ForegroundColor Cyan
docker-compose build mineru

# 7. 启动服务
Write-Host "启动所有服务..." -ForegroundColor Cyan
docker-compose up -d

# 8. 显示状态
docker-compose ps
docker-compose logs --tail=50 mineru
```

## 成功标志

构建成功后应该看到:

```
[+] Building 120.5s (15/15) FINISHED
 => [internal] load build definition
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/ubuntu:22.04
 => [1/10] FROM docker.io/library/ubuntu:22.04
 => exporting to image
 => => naming to docker.io/library/cotstudio-mineru
```

## 下一步

构建成功后:

```powershell
# 查看MinerU日志(首次启动会下载模型)
docker-compose logs -f mineru

# 等待模型下载完成后,测试健康检查
Invoke-WebRequest -Uri http://localhost:8001/health

# 应该返回:
# {"status":"healthy","service":"MinerU","version":"2.5.0"}
```

## 获取帮助

如果问题仍未解决,请提供:

```powershell
# 1. Docker版本
docker --version
docker-compose --version

# 2. 配置内容
Get-Content $env:USERPROFILE\.docker\config.json

# 3. 环境变量
echo "HTTP_PROXY: $env:HTTP_PROXY"
echo "DOCKER_BUILDKIT: $env:DOCKER_BUILDKIT"

# 4. 完整错误日志
docker-compose build mineru 2>&1 | Tee-Object -FilePath build-error.log
```
