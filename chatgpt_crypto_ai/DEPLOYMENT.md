# CoinGPT 部署指南

本文档提供了将CoinGPT部署到生产环境的详细说明。

## 本地部署

### 使用 Python 内置服务器 (开发环境)

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 设置环境变量:
   ```bash
   cp .env.example .env
   # 编辑.env文件，填写必要的API密钥和配置
   ```

3. 启动应用:
   ```bash
   python run.py
   ```

4. 访问 `http://localhost:5000`

### 使用 Gunicorn (生产环境)

1. 安装依赖，包括gunicorn:
   ```bash
   pip install -r requirements.txt gunicorn
   ```

2. 设置环境变量同上

3. 使用gunicorn启动:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'
   ```

## Docker部署

1. 构建Docker镜像:
   ```bash
   docker build -t coingpt .
   ```

2. 运行容器:
   ```bash
   docker run -d -p 5000:5000 --env-file .env --name coingpt-container coingpt
   ```

## 云服务部署

### Heroku

1. 安装Heroku CLI并登录

2. 初始化Git仓库:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

3. 创建Heroku应用:
   ```bash
   heroku create your-app-name
   ```

4. 设置环境变量:
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set EXCHANGE_API_KEY=your_key
   heroku config:set EXCHANGE_SECRET=your_secret
   heroku config:set SECRET_KEY=your_secret_key
   ```

5. 部署:
   ```bash
   git push heroku main
   ```

### AWS Elastic Beanstalk

1. 安装EB CLI并配置

2. 初始化EB项目:
   ```bash
   eb init
   ```

3. 创建环境:
   ```bash
   eb create coingpt-env
   ```

4. 设置环境变量:
   ```bash
   eb setenv OPENAI_API_KEY=your_key EXCHANGE_API_KEY=your_key EXCHANGE_SECRET=your_secret SECRET_KEY=your_secret_key
   ```

5. 部署:
   ```bash
   eb deploy
   ```

## 配置 Nginx 反向代理

为了在生产环境使用HTTPS并提高性能，建议配置Nginx作为反向代理。

示例Nginx配置:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向HTTP到HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 安全注意事项

1. 永远不要在代码中硬编码API密钥和敏感信息，使用环境变量
2. 在生产环境中禁用DEBUG模式
3. 使用强密码作为SECRET_KEY
4. 定期更新依赖以修复安全漏洞
5. 考虑使用HTTPS确保数据传输安全

## 生产环��监控

考虑使用以下工具监控生产环境:
- Prometheus + Grafana 用于性能监控
- Sentry 用于错误跟踪
- NewRelic 或 DataDog 用于APM监控
