# Docker 部署

## 快速开始

### 1. 拉取镜像

```bash
docker pull smartresume:latest
```

### 2. 运行容器

```bash
docker run -d --name smartresume -p 8000:8000 smartresume:latest
```

### 3. 使用 Docker Compose

```yaml
version: '3.8'
services:
  smartresume:
    image: smartresume:latest
    ports:
      - "8000:8000"
```

## 下一步

- [学习基本使用](../usage/index.md)
- [了解配置选项](../usage/configuration.md)