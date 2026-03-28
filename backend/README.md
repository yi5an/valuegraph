# ValueGraph Backend

> 价值投资知识图谱平台后端 API

## 📋 项目简介

ValueGraph 是一个基于价值投资理念的股票分析平台，提供：

- **价值推荐**：基于 ROE、负债率等指标筛选优质股票
- **财报分析**：5 年财务数据时间线展示
- **持股查询**：十大股东 + 机构持仓信息

## 🛠️ 技术栈

- **框架**：FastAPI 0.109+
- **数据库**：SQLite（MVP）+ SQLAlchemy ORM
- **数据源**：AkShare（免费 A 股数据）
- **缓存**：Redis（可选）
- **限流**：SlowAPI

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/projects/valuegraph/backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. 访问文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API 接口

### 1. 价值推荐

```http
GET /api/stocks/recommend?market=A&limit=20&min_roe=15&max_debt_ratio=50
```

**参数**：
- `market`: 市场类型（A=A股，US=美股，HK=港股）
- `limit`: 返回数量（1-100）
- `min_roe`: 最低 ROE（%）
- `max_debt_ratio`: 最高负债率（%）
- `industry`: 行业筛选（可选）

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "stock_code": "600519",
      "name": "贵州茅台",
      "market": "A",
      "industry": "白酒",
      "latest_roe": 28.56,
      "debt_ratio": 25.0,
      "recommendation_score": 95,
      "recommendation_reason": "高ROE、低负债、估值合理"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "limit": 20
  }
}
```

### 2. 财报分析

```http
GET /api/financials/600519?years=5
```

**参数**：
- `stock_code`: 股票代码（路径参数）
- `years`: 查询年数（1-10）

**响应示例**：
```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "name": "贵州茅台",
    "timeline": [
      {
        "report_date": "2025-12-31",
        "roe": 28.56,
        "gross_margin": 91.23,
        "debt_ratio": 25.0,
        "revenue": 127500000000,
        "net_profit": 62500000000
      }
    ],
    "health_score": {
      "overall": 92,
      "profitability": 95,
      "solvency": 90,
      "growth": 88,
      "operation": 94
    }
  }
}
```

### 3. 持股查询

```http
GET /api/shareholders/600519
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "name": "贵州茅台",
    "top_10_shareholders": [
      {
        "rank": 1,
        "holder_name": "中国贵州茅台酒厂(集团)有限责任公司",
        "hold_amount": 6780000000,
        "hold_ratio": 54.06,
        "holder_type": "国有法人",
        "change": "不变"
      }
    ],
    "institutional_holders": []
  }
}
```

### 4. 同步股票列表（管理员）

```http
POST /api/stocks/sync?market=A
```

## 🗂️ 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   │   ├── stock.py
│   │   ├── financial.py
│   │   └── shareholder.py
│   ├── schemas/             # Pydantic 模型
│   │   ├── stock.py
│   │   ├── financial.py
│   │   └── shareholder.py
│   ├── api/                 # API 路由
│   │   ├── stocks.py
│   │   ├── financials.py
│   │   └── shareholders.py
│   ├── services/            # 业务逻辑
│   │   ├── recommendation.py
│   │   ├── financial_analysis.py
│   │   └── data_collector.py
│   └── utils/
│       ├── cache.py         # Redis 缓存
│       └── rate_limiter.py  # 限流器
├── requirements.txt
└── README.md
```

## ⚙️ 配置说明

创建 `.env` 文件（可选）：

```env
# 应用配置
APP_NAME=ValueGraph
DEBUG=True

# 数据库配置
DATABASE_URL=sqlite:///./valuegraph.db

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=False

# 缓存配置
CACHE_TTL=3600

# 限流配置
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
```

## 🔧 开发指南

### 运行测试

```bash
pytest tests/
```

### 数据库迁移

```bash
# 初始化数据库（自动执行）
python -c "from app.database import init_db; init_db()"
```

### 同步股票数据

```bash
# 通过 API 同步
curl -X POST http://localhost:8000/api/stocks/sync?market=A
```

## 📊 性能优化

- **缓存**：Redis 缓存热门查询（1 小时）
- **限流**：60 次/分钟（防止滥用）
- **索引**：数据库关键字段建立索引
- **懒加载**：财报数据按需从 AkShare 获取

## ⚠️ 注意事项

1. **AkShare 限流**：AkShare 是免费接口，频繁调用可能被封禁
2. **数据延迟**：财报数据有 1-3 天延迟
3. **SQLite 限制**：MVP 使用 SQLite，生产环境建议 PostgreSQL
4. **Redis 可选**：MVP 阶段可禁用 Redis

## 🚧 后续计划

- [ ] 支持美股、港股市场
- [ ] 集成 Neo4j 知识图谱
- [ ] 添加新闻聚合功能
- [ ] 实现智能问答（RAG）
- [ ] 迁移到 PostgreSQL

## 📝 更新日志

### v1.0.0 (2026-03-24)
- ✅ 初始化项目
- ✅ 实现价值推荐 API
- ✅ 实现财报分析 API
- ✅ 实现持股查询 API
- ✅ 集成 AkShare 数据源
- ✅ 添加缓存和限流

---

**开发者**：Coder  
**架构师**：Architect  
**产品经理**：德国
