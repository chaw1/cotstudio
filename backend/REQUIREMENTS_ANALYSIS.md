# Requirements.txt 包分析报告

## 🚨 问题包识别

### 1. 认证相关问题包
```python
jwt==1.4.0          # ❌ 问题：过时包，与PyJWT冲突
jose==1.0.0         # ❌ 问题：过时包，与python-jose冲突
PyJWT[cryptography]==2.8.0  # ⚠️  版本过旧，建议使用最新版
```

**问题原因**:
- `jwt` 和 `jose` 是过时的包，与现代的 `PyJWT` 和 `python-jose` 冲突
- 这些包在安装时会产生依赖冲突

**解决方案**:
```python
# 只保留 PyJWT，移除 jwt 和 jose
PyJWT[cryptography]  # 使用最新版本
```

### 2. OCR 相关大型包
```python
paddlepaddle==3.2.0  # ❌ 问题：体积巨大(~500MB)，下载容易超时
paddleocr==2.7.3     # ❌ 问题：依赖paddlepaddle，安装复杂
```

**问题原因**:
- PaddlePaddle 是一个完整的深度学习框架，体积非常大
- 在网络不稳定的情况下很容易下载超时
- 编译依赖复杂，容易出现编译错误

**解决方案**:
```python
# 方案1：移除OCR功能，后续按需添加
# paddlepaddle
# paddleocr

# 方案2：使用轻量级OCR库
# easyocr  # 更轻量的选择
# pytesseract  # 基于Tesseract的OCR
```

### 3. 安全扫描包
```python
yara-python==4.3.1  # ❌ 问题：需要编译，Windows上容易失败
```

**问题原因**:
- 需要编译C扩展
- 在Windows环境下需要Visual Studio构建工具
- 不是核心功能，可以暂时移除

**解决方案**:
```python
# 暂时移除，后续按需添加
# yara-python
```

### 4. LangChain 版本问题
```python
langchain==0.0.350      # ⚠️  版本过旧
langchain-openai==0.0.2 # ⚠️  版本过旧
```

**问题原因**:
- LangChain 发展很快，旧版本可能有兼容性问题
- 建议使用最新稳定版本

**解决方案**:
```python
langchain        # 使用最新版本
langchain-openai # 使用最新版本
```

## ✅ 优化后的依赖策略

### 核心原则
1. **移除冲突包**: 删除 `jwt`, `jose` 等冲突包
2. **使用最新版本**: 不固定版本号，使用最新稳定版
3. **移除大型包**: 暂时移除 PaddlePaddle 等大型包
4. **保留核心功能**: 确保 FastAPI、数据库、认证等核心功能正常

### 分阶段安装策略

#### 阶段1：核心依赖 (必需)
```python
# 核心Web框架
fastapi
uvicorn[standard]
pydantic
pydantic-settings

# 数据库
sqlalchemy
alembic
psycopg2-binary
neo4j

# 认证
PyJWT[cryptography]
passlib[bcrypt]
```

#### 阶段2：扩展功能 (可选)
```python
# 异步任务
celery
redis

# 文件处理
Pillow
pdf2image

# LLM集成
openai
langchain
langchain-openai
```

#### 阶段3：开发工具 (开发环境)
```python
# 测试
pytest
pytest-asyncio
pytest-cov

# 代码质量
black
isort
flake8
```

## 🔧 安装建议

### 方法1：使用优化的requirements文件
```bash
pip install -r requirements-latest.txt
```

### 方法2：分阶段安装
```bash
# 先安装核心依赖
pip install fastapi uvicorn[standard] pydantic sqlalchemy psycopg2-binary

# 再安装扩展功能
pip install celery redis neo4j openai

# 最后安装开发工具
pip install pytest black flake8
```

### 方法3：使用国内镜像源
```bash
pip install -r requirements-latest.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📊 包大小对比

| 包名 | 大小 | 安装时间 | 问题风险 |
|------|------|----------|----------|
| paddlepaddle | ~500MB | 5-10分钟 | 高 |
| paddleocr | ~50MB | 1-2分钟 | 中 |
| yara-python | ~5MB | 30秒-5分钟 | 高(编译) |
| jwt + jose | ~1MB | 10秒 | 高(冲突) |
| langchain | ~20MB | 30秒 | 低 |

## 🎯 推荐配置

### 生产环境
```python
# 使用 requirements-latest.txt
# 移除所有问题包
# 使用最新稳定版本
```

### 开发环境
```python
# 可以尝试完整的 requirements.txt
# 如果安装失败，回退到 requirements-latest.txt
```

### Docker环境
```python
# 推荐使用 requirements-latest.txt
# 在Dockerfile中分阶段安装
# 使用多阶段构建优化镜像大小
```

## 🔄 后续添加策略

### OCR功能
```python
# 当需要OCR功能时，可以选择：
easyocr          # 轻量级，支持多语言
pytesseract      # 基于Tesseract，稳定
paddleocr        # 功能强大，但体积大
```

### 安全扫描
```python
# 当需要安全扫描时：
bandit           # Python安全检查
safety           # 依赖安全检查
# yara-python    # 恶意软件检测（需要编译环境）
```

---

**建议**: 先使用 `requirements-latest.txt` 确保基本功能正常，然后根据实际需求逐步添加其他功能包。