FROM node:22-alpine

WORKDIR /app

# 安装 nodemon（开发环境）
RUN npm install -g nodemon

# 使用国内源（可选）
RUN npm config set registry https://registry.npmmirror.com

# 复制依赖文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm install

# 复制代码（不包含 node_modules，因为 .dockerignore 会忽略）
COPY . .

# 复制 .env.docker 到容器，并重命名为 .env
COPY .env.docker .env

EXPOSE 8000

CMD ["nodemon", "server.js"]
