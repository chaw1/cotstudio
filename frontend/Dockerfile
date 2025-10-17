# 多阶段构建
FROM node:20-alpine as base

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 开发环境阶段
FROM base as development

# 安装所有依赖（包括开发依赖）
RUN npm ci

# 复制源代码
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# 构建阶段
FROM base as builder

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产环境镜像
FROM nginx:alpine as production

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]