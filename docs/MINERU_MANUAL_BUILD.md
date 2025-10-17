# MinerU 手动构建镜像指南
# 适用于网络严重受限的环境

## 方法: 交互式构建镜像

这种方法通过在运行的容器中手动安装包,然后保存为镜像。

### 步骤 1: 启动临时Python容器

```powershell
# 启动交互式容器
docker run -it --name mineru-build python:3.10-slim bash
```

### 步骤 2: 在容器内安装依赖

在容器的bash提示符下执行:

```bash
# 1. 配置pip镜像源(清华大学)
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn
pip config set global.timeout 300

# 2. 更新pip
pip install --upgrade pip

# 3. 安装MinerU核心
pip install mineru

# 4. 安装Web服务依赖
pip install fastapi
pip install "uvicorn[standard]"
pip install python-multipart

# 5. 安装图像处理
pip install opencv-python-headless

# 6. 安装HTTP客户端
pip install requests

# 7. 安装PyTorch (CPU版本)
pip install torch

# 8. 创建必要目录
mkdir -p /app/models /app/temp /app/output
cd /app

# 9. 创建用户
useradd -m -u 1000 mineru
chown -R mineru:mineru /app

# 10. 测试安装
python -c "import mineru; print('MinerU installed successfully!')"
python -c "import fastapi; print('FastAPI installed successfully!')"

# 11. 退出容器
exit
```

### 步骤 3: 保存容器为镜像

```powershell
# 将容器保存为镜像
docker commit mineru-build cotstudio-mineru:latest

# 查看镜像
docker images cotstudio-mineru

# 清理临时容器
docker rm mineru-build
```

### 步骤 4: 添加服务文件

创建一个脚本来启动容器并复制文件:

```powershell
# 启动容器
docker run -d --name mineru-service `
  -p 8001:8001 `
  -v mineru_models:/app/models `
  -v mineru_temp:/app/temp `
  -v mineru_output:/app/output `
  cotstudio-mineru:latest `
  tail -f /dev/null

# 复制服务文件
docker cp .\docker\mineru\mineru_service.py mineru-service:/app/

# 重启容器并运行服务
docker restart mineru-service
docker exec -d mineru-service python /app/mineru_service.py

# 查看日志
docker logs -f mineru-service
```

### 步骤 5: 测试服务

```powershell
# 测试健康检查
Invoke-WebRequest -Uri http://localhost:8001/health

# 应该返回:
# {"status":"healthy","service":"MinerU","version":"2.5.0"}
```

---

## 方法2: 使用预下载的whl文件

如果pip在线安装完全失败,可以预先下载whl文件:

### 在网络正常的机器上:

```bash
# 创建目录
mkdir mineru-wheels
cd mineru-wheels

# 下载所有依赖
pip download mineru fastapi uvicorn python-multipart opencv-python-headless requests torch

# 打包传输
tar -czf mineru-wheels.tar.gz *.whl
```

### 在目标机器上:

```powershell
# 解压
tar -xzf mineru-wheels.tar.gz

# 启动容器并挂载whl目录
docker run -it --name mineru-build `
  -v ${PWD}:/wheels `
  python:3.10-slim bash

# 在容器内安装
cd /wheels
pip install --no-index --find-links . *.whl

# 其余步骤同方法1
```

---

## 方法3: 完整的预构建镜像

如果您有另一台网络正常的机器:

### 在网络正常的机器上:

```bash
# 1. 克隆或复制项目
cd cotstudio

# 2. 修改Dockerfile.minimal移除代理设置
# 编辑: docker/mineru/Dockerfile.minimal
# 确保没有HTTP_PROXY相关配置

# 3. 构建镜像
docker-compose build mineru

# 4. 导出镜像
docker save -o mineru-complete.tar cotstudio-mineru:latest

# 5. 压缩以减小体积
gzip mineru-complete.tar
# 结果: mineru-complete.tar.gz (约1-1.5GB)

# 6. 传输到目标机器
```

### 在目标机器上:

```powershell
# 1. 解压
gzip -d mineru-complete.tar.gz

# 2. 加载镜像
docker load -i mineru-complete.tar

# 3. 查看镜像
docker images cotstudio-mineru

# 4. 启动服务(使用docker-compose)
docker-compose up -d mineru

# 或手动启动
docker run -d --name mineru `
  -p 8001:8001 `
  -v mineru_models:/app/models `
  -v mineru_temp:/app/temp `
  -v mineru_output:/app/output `
  --restart unless-stopped `
  cotstudio-mineru:latest
```

---

## 推荐流程

基于您的当前情况,推荐以下流程:

### 选项 A: 使用另一台机器(最推荐)

1. ✅ 在网络正常的机器上完整构建
2. ✅ 导出镜像文件
3. ✅ 传输并加载到目标机器
4. ✅ 直接启动,无需再次构建

**优点**: 最稳定,一次成功
**缺点**: 需要另一台机器和传输时间

### 选项 B: 交互式手动构建(当前可行)

1. ✅ 不需要其他机器
2. ✅ 在容器内手动pip install
3. ✅ commit保存为镜像
4. ✅ 手动启动容器

**优点**: 完全本地操作,可控
**缺点**: 步骤较多,需要手动操作

### 选项 C: 下载whl文件

1. ✅ 预先下载所有依赖包
2. ✅ 离线安装
3. ✅ commit保存

**优点**: 完全离线
**缺点**: 需要额外下载步骤

---

## 立即执行(推荐选项B)

```powershell
# 第1步: 启动容器
docker run -it --name mineru-build python:3.10-slim bash

# 第2步: 在容器内逐个安装(复制粘贴下面的命令)
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install mineru
pip install fastapi uvicorn python-multipart opencv-python-headless requests torch
mkdir -p /app/models /app/temp /app/output
useradd -m mineru
chown -R mineru:mineru /app
exit

# 第3步: 保存为镜像
docker commit mineru-build cotstudio-mineru:latest
docker rm mineru-build

# 第4步: 复制服务文件并启动
docker run -d --name mineru -p 8001:8001 `
  -v mineru_models:/app/models `
  cotstudio-mineru:latest tail -f /dev/null

docker cp .\docker\mineru\mineru_service.py mineru:/app/
docker restart mineru
docker exec -d -u mineru mineru python /app/mineru_service.py

# 第5步: 测试
Start-Sleep -Seconds 10
Invoke-WebRequest http://localhost:8001/health
```

---

## 下一步

请选择您偏好的方案:

1. **如果有另一台网络正常的机器** → 使用方法3
2. **如果只能用当前机器** → 使用方法1(交互式构建)
3. **如果完全无网络** → 使用方法2(whl文件)

我可以为您创建自动化脚本来执行选定的方案。请告诉我您的选择! 🚀
