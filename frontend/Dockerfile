# syntax=docker/dockerfile:1
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json /app/
# 使用淘宝 npm 镜像 + BuildKit 缓存
RUN --mount=type=cache,target=/root/.npm \
    npm ci --registry=https://registry.npmmirror.com

COPY . /app
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
