# ValueGraph - 价值投资知识图谱平台

## 项目简介
基于 FastAPI 的多市场价值投资推荐系统，支持 A 股和美股市场。

## MVP 功能
1. 多市场价值投资推荐（A股+美股）
2. 财报深度分析
3. 持股信息查询

## 技术栈
- **后端框架**: FastAPI
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **数据源**: Tushare Pro API
- **任务队列**: Celery

## 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r backend/requirements.txt
```

### 2. 配置环境变量
复制 `backend/.env` 并填入您的 Tushare Token

### 3. 启动服务
```bash
docker-compose up -d
```

### 4. 访问 API
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

## 项目结构
```
valuegraph/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── models/          # 数据模型
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务逻辑
│   │   └── utils/           # 工具函数
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 开发进度
- [x] 项目初始化
- [x] Tushare API 测试
- [ ] 数据库设计
- [ ] API 接口开发
- [ ] 前端集成

## 协作
- 数据库设计: @architect
- API 接口: @frontenddev
