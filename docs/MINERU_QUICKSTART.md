# MinerU 2.5 快速启动指南

## 🚀 5分钟快速部署

### 前提条件
- Docker和docker-compose已安装
- (可选) NVIDIA GPU + CUDA 12.1+

### 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd cotstudio

# 给脚本执行权限
chmod +x scripts/deploy_mineru.sh

# 运行部署脚本
./scripts/deploy_mineru.sh
```

脚本会自动:
- ✅ 检测GPU环境
- ✅ 选择最佳部署模式(GPU/CPU)
- ✅ 下载必要的模型文件
- ✅ 构建和启动服务
- ✅ 验证服务状态

### 手动部署 (GPU模式)

```bash
# 构建并启动所有服务
docker-compose up -d

# 等待MinerU服务就绪 (首次需要10-20分钟下载模型)
docker-compose logs -f mineru

# 验证服务
curl http://localhost:8001/health
```

### 手动部署 (CPU模式)

```bash
# 使用CPU配置
docker-compose -f docker-compose.yml -f docker-compose.cpu.yml up -d

# 查看日志
docker-compose logs -f mineru
```

## ✅ 验证部署

### 1. 检查服务状态

```bash
# 查看所有服务
docker-compose ps

# 预期输出:
# mineru     ... Up (healthy)   8001/tcp
# backend    ... Up (healthy)   8000/tcp
# frontend   ... Up (healthy)   3000/tcp
```

### 2. 测试MinerU服务

```bash
# 健康检查
curl http://localhost:8001/health | python -m json.tool

# 预期输出:
# {
#   "status": "healthy",
#   "mineru_ready": true,
#   "gpu_available": true,
#   "gpu_count": 1
# }
```

### 3. 测试OCR功能

```bash
# 使用测试脚本
python scripts/test_mineru.py /path/to/your/test.pdf

# 或手动测试
curl -X POST http://localhost:8001/ocr \
  -F "file=@test.pdf" \
  -F "backend=pipeline" \
  -F "device=cuda"
```

## 🎯 在Web界面中使用

1. 打开浏览器访问 `http://localhost:3000`
2. 登录系统
3. 进入 **系统设置 → OCR引擎**
4. 找到 **MinerU** 引擎
5. 点击 **配置** 按钮
6. 设置参数:
   - 启用引擎: ✅
   - 优先级: 1 (最高)
   - Backend: `pipeline` (快速) 或 `vlm-transformers` (高精度)
   - Device: `cuda` (GPU) 或 `cpu`
7. 保存配置

## 📊 性能对比

| 模式 | 10页PDF处理时间 | 精度 |
|------|----------------|------|
| GPU + pipeline | ~15秒 | 98% |
| GPU + vlm | ~30秒 | 99% |
| CPU + pipeline | ~2分钟 | 98% |
| CPU + vlm | ~5分钟 | 99% |

## 🔧 常见问题

### Q1: MinerU服务一直显示"starting"

**A:** 首次启动需要下载模型(8-12GB),请耐心等待。查看进度:
```bash
docker-compose logs -f mineru | grep "下载"
```

### Q2: GPU不可用

**A:** 检查NVIDIA Container Toolkit:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

如果失败,安装toolkit:
```bash
sudo apt-get install nvidia-container-toolkit
sudo systemctl restart docker
```

### Q3: 内存不足

**A:** MinerU需要:
- GPU模式: 6GB+ GPU显存
- CPU模式: 8GB+ 系统内存

可以调整batch_size减少内存占用。

### Q4: 网络下载模型太慢

**A:** 使用离线部署:
1. 在本地下载模型
2. 上传到服务器
3. 挂载到Docker卷

详见 `docs/MINERU_DEPLOYMENT.md`

## 📚 完整文档

- [MinerU部署完整指南](../docs/MINERU_DEPLOYMENT.md)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [项目主文档](../README.md)

## 🆘 获取帮助

遇到问题? 提供以下信息:

```bash
# 收集诊断信息
docker-compose ps
docker-compose logs mineru --tail=100
curl http://localhost:8001/health
nvidia-smi  # 如使用GPU
```

---

**快速部署完成!** 🎉

下一步: 在系统设置中配置MinerU引擎,然后上传PDF测试OCR功能。
