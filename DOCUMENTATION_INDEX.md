# COT Studio MVP 文档索引

## 📖 文档概览

本项目包含完整的文档体系，涵盖从快速开始到深度开发的各个方面。

## 🚀 快速开始

### 新用户必读
1. **[README.md](README.md)** - 项目概述和快速开始
2. **[PROJECT_GUIDE.md](PROJECT_GUIDE.md)** - 完整项目指南 ⭐ **推荐首读**

### 安装和部署
3. **[docs/INSTALLATION.md](docs/INSTALLATION.md)** - 详细安装指南
4. **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - 生产环境部署
5. **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - 故障排除指南

## 🛠️ 开发文档

### 开发指南
6. **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - 开发环境和规范
7. **[test-documentation.md](test-documentation.md)** - 测试策略和实施

### 交付文档
8. **[DELIVERY_PACKAGE.md](DELIVERY_PACKAGE.md)** - 完整交付包说明

## 📋 文档使用指南

### 根据角色选择文档

#### 🆕 新用户 / 体验者
```
README.md → PROJECT_GUIDE.md → docs/INSTALLATION.md
```
- 了解项目概况
- 快速安装和体验
- 学习基本使用方法

#### 👨‍💻 开发者
```
PROJECT_GUIDE.md → docs/DEVELOPMENT.md → test-documentation.md
```
- 理解系统架构
- 搭建开发环境
- 学习开发规范和测试

#### 🚀 运维人员
```
docs/INSTALLATION.md → docs/DEPLOYMENT.md → docs/TROUBLESHOOTING.md
```
- 掌握安装部署流程
- 了解生产环境配置
- 学习故障排除方法

#### 📊 项目经理 / 技术负责人
```
DELIVERY_PACKAGE.md → PROJECT_GUIDE.md → README.md
```
- 了解交付内容
- 掌握技术架构
- 评估项目状态

## 🔍 按主题查找

### 环境配置
- **快速配置**: [README.md](README.md#环境配置)
- **网络配置**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#网络配置) ⚠️ **镜像下载问题必看**
- **详细配置**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#环境配置)
- **生产配置**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### 用户认证
- **默认凭据**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#访问服务)
- **用户管理**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#用户账户)

### API 使用
- **API 概览**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#api-文档)
- **在线文档**: http://localhost:8000/docs (需启动服务)

### 故障排除
- **Docker 镜像下载问题**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#docker-镜像下载失败) ⚠️ **最常见问题**
- **Docker 构建失败问题**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#docker-构建失败) ⚠️ **pip install 错误**
- **常见问题**: [README.md](README.md#故障排除)
- **详细指南**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **开发问题**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#常见问题)

### 系统架构
- **架构概览**: [README.md](README.md#架构概览)
- **技术栈**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md#系统架构)
- **服务详情**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#服务详情)

## 📊 配置参考

### 统一配置标准

#### 服务凭据
| 服务 | 用户名 | 密码 | 端口 |
|------|--------|------|------|
| PostgreSQL | cotuser | cotpass | 5432 |
| Neo4j | neo4j | neo4jpass | 7474/7687 |
| Redis | - | redispass | 6379 |
| MinIO | minioadmin | minioadmin123 | 9000/9001 |
| RabbitMQ | cotuser | cotpass | 5672/15672 |

#### 应用用户
| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | 971028 | 超级管理员 |
| 编辑者 | editor | secret | 编辑者 |

#### 必需环境变量
```env
# LLM API 密钥 (至少配置一个)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
KIMI_API_KEY=your-kimi-api-key-here

# 应用安全密钥 (生产环境必须修改)
SECRET_KEY=your-secret-key-change-in-production-please-use-a-strong-key
```

## 🔗 外部资源

### 在线服务 (需启动应用)
- **前端应用**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **Neo4j 浏览器**: http://localhost:7474
- **MinIO 控制台**: http://localhost:9001
- **RabbitMQ 管理**: http://localhost:15672
- **Celery 监控**: http://localhost:5555

### 技术文档
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Docker**: https://docs.docker.com/
- **Neo4j**: https://neo4j.com/docs/

## 📝 文档维护

### 文档更新原则
1. **及时性**: 代码变更后及时更新相关文档
2. **准确性**: 确保文档内容与实际实现一致
3. **完整性**: 新功能必须包含相应文档
4. **易读性**: 使用清晰的结构和示例

### 文档贡献
- 发现文档问题请提交 Issue
- 欢迎提交 PR 改进文档
- 遵循现有文档的格式和风格

## 📞 获取帮助

### 问题解决流程
1. **查阅文档**: 首先查看相关文档
2. **搜索 Issues**: 在 GitHub 上搜索类似问题
3. **提交 Issue**: 提供详细的问题描述和环境信息
4. **联系团队**: 紧急问题可直接联系开发团队

### 反馈渠道
- **GitHub Issues**: 技术问题和 bug 报告
- **GitHub Discussions**: 功能建议和讨论
- **Email**: 商务合作和其他事宜

---

**文档版本**: 1.0.0  
**最后更新**: 2025-01-17  
**维护团队**: COT Studio 开发团队

> 💡 **提示**: 建议将本文档加入书签，方便快速查找所需信息。