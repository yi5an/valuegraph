# ValueGraph 系统架构设计

> 版本：v1.0  
> 日期：2026-03-22  
> 作者：Architect  
> 状态：MVP 架构设计完成

---

## 1. 系统架构概览

### 1.1 整体架构图（Mermaid）

```mermaid
graph TB
    subgraph "数据源层 Data Sources"
        TS[Tushare Pro API<br/>A股数据]
        YF[Yahoo Finance API<br/>美股数据]
    end

    subgraph "数据采集层 Data Collection"
        CW[Celery Workers<br/>异步任务调度]
        RQ[(Redis<br/>任务队列)]
        CC[Data Collectors<br/>数据采集器]
    end

    subgraph "后端服务层 Backend API"
        FA[FastAPI Server<br/>REST API]
        BL[Business Logic<br/>业务逻辑层]
        CA[Cache Layer<br/>Redis缓存]
    end

    subgraph "数据存储层 Data Storage"
        PG[(PostgreSQL 15+<br/>关系数据)]
        N4[(Neo4j 5.x<br/>知识图谱<br/>v1.5+)]
        MG[(MongoDB 6.x<br/>新闻存储<br/>v1.5+)]
        MV[(Milvus 2.x<br/>向量搜索<br/>v1.5+)]
    end

    subgraph "前端展示层 Frontend"
        NX[Next.js 14+<br/>React + TypeScript]
        AD[Ant Design 5.x<br/>UI组件库]
        EC[ECharts 5.x<br/>图表可视化]
        G6[G6<br/>知识图谱可视化]
    end

    TS --> CC
    YF --> CC
    CW --> RQ
    RQ --> CC
    CC --> PG
    
    FA --> BL
    BL --> CA
    BL --> PG
    CA -.-> PG
    
    NX --> FA
    AD --> NX
    EC --> NX
    G6 --> NX
    
    style FA fill:#4CAF50,stroke:#2E7D32,color:#fff
    style PG fill:#336791,stroke:#1D4E79,color:#fff
    style N4 fill:#018BFF,stroke:#0066CC,color:#fff
    style NX fill:#000,stroke:#333,color:#fff
```

### 1.2 数据流向

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as FastAPI
    participant Cache as Redis
    participant DB as PostgreSQL
    participant Celery
    participant Tushare

    User->>Frontend: 查询股票推荐
    Frontend->>API: GET /api/stocks/recommend
    API->>Cache: 检查缓存
    
    alt 缓存命中
        Cache-->>API: 返回缓存数据
    else 缓存未命中
        API->>DB: 查询数据库
        DB-->>API: 返回结果
        API->>Cache: 写入缓存
    end
    
    API-->>Frontend: JSON响应
    Frontend-->>User: 展示推荐列表

    Note over Celery,Tushare: 后台数据更新（定时任务）
    Celery->>Tushare: 获取最新数据
    Tushare-->>Celery: 返回数据
    Celery->>DB: 更新数据库
```

---

## 2. 数据库设计（PostgreSQL）

### 2.1 ER 图

```mermaid
erDiagram
    STOCKS ||--o{ STOCK_PRICES : has
    STOCKS ||--o{ FINANCIALS : has
    STOCKS ||--o{ SHAREHOLDERS : has
    STOCKS ||--o{ TOP_HOLDERS : has

    STOCKS {
        varchar stock_code PK "股票代码"
        varchar market "市场(A/US)"
        varchar name "股票名称"
        varchar industry "所属行业"
        varchar sector "所属板块"
        decimal market_cap "市值"
        timestamp listed_date "上市日期"
        timestamp created_at
        timestamp updated_at
    }

    STOCK_PRICES {
        bigint id PK
        varchar stock_code FK
        date trade_date "交易日期"
        decimal open "开盘价"
        decimal high "最高价"
        decimal low "最低价"
        decimal close "收盘价"
        bigint volume "成交量"
        decimal amount "成交额"
        decimal change_pct "涨跌幅%"
        timestamp created_at
    }

    FINANCIALS {
        bigint id PK
        varchar stock_code FK
        date report_date "报告期"
        varchar report_type "报告类型"
        decimal revenue "营业收入"
        decimal net_profit "净利润"
        decimal total_assets "总资产"
        decimal total_liabilities "总负债"
        decimal roe "净资产收益率"
        decimal gross_margin "毛利率"
        decimal operating_cash_flow "经营现金流"
        decimal eps "每股收益"
        decimal bvps "每股净资产"
        timestamp created_at
    }

    SHAREHOLDERS {
        bigint id PK
        varchar stock_code FK
        date report_date "报告期"
        varchar holder_name "股东名称"
        bigint hold_amount "持股数量"
        decimal hold_ratio "持股比例%"
        int rank "排名"
        varchar holder_type "股东类型"
        timestamp created_at
    }

    TOP_HOLDERS {
        bigint id PK
        varchar stock_code FK
        date report_date "报告期"
        varchar institution_name "机构名称"
        bigint hold_amount "持股数量"
        decimal hold_ratio "持股比例%"
        varchar institution_type "机构类型"
        timestamp created_at
    }
```

### 2.2 SQL Schema

```sql
-- 股票基础信息表
CREATE TABLE stocks (
    stock_code VARCHAR(20) PRIMARY KEY,
    market VARCHAR(10) NOT NULL CHECK (market IN ('A', 'US')),
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    sector VARCHAR(50),
    market_cap DECIMAL(18, 2),
    listed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stocks_market ON stocks(market);
CREATE INDEX idx_stocks_industry ON stocks(industry);

-- 股价数据表（分区表，按年份分区）
CREATE TABLE stock_prices (
    id BIGSERIAL,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    trade_date DATE NOT NULL,
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4),
    volume BIGINT,
    amount DECIMAL(18, 2),
    change_pct DECIMAL(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, trade_date)
) PARTITION BY RANGE (trade_date);

-- 创建 2026 年分区
CREATE TABLE stock_prices_2026 PARTITION OF stock_prices
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX idx_stock_prices_code_date ON stock_prices(stock_code, trade_date DESC);

-- 财报数据表
CREATE TABLE financials (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    report_date DATE NOT NULL,
    report_type VARCHAR(20) CHECK (report_type IN ('Q1', 'Q2', 'Q3', 'annual')),
    revenue DECIMAL(18, 2),
    net_profit DECIMAL(18, 2),
    total_assets DECIMAL(18, 2),
    total_liabilities DECIMAL(18, 2),
    roe DECIMAL(8, 4),
    gross_margin DECIMAL(8, 4),
    operating_cash_flow DECIMAL(18, 2),
    eps DECIMAL(10, 4),
    bvps DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, report_date, report_type)
);

CREATE INDEX idx_financials_code_date ON financials(stock_code, report_date DESC);

-- 十大股东表
CREATE TABLE shareholders (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    report_date DATE NOT NULL,
    holder_name VARCHAR(200) NOT NULL,
    hold_amount BIGINT,
    hold_ratio DECIMAL(8, 4),
    rank INTEGER,
    holder_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shareholders_code_date ON shareholders(stock_code, report_date DESC);
CREATE INDEX idx_shareholders_holder ON shareholders(holder_name);

-- 机构持仓表
CREATE TABLE top_holders (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    report_date DATE NOT NULL,
    institution_name VARCHAR(200) NOT NULL,
    hold_amount BIGINT,
    hold_ratio DECIMAL(8, 4),
    institution_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_top_holders_code_date ON top_holders(stock_code, report_date DESC);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stocks_updated_at
    BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## 3. API 接口设计

### 3.1 API 概览

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/api/stocks/recommend` | GET | 获取价值投资推荐列表 | 可选 |
| `/api/stocks/:code` | GET | 获取股票详细信息 | 可选 |
| `/api/financials/:code` | GET | 获取财报数据（时间线） | 可选 |
| `/api/shareholders/:code` | GET | 获取股东信息 | 可选 |
| `/api/prices/:code` | GET | 获取股价历史数据 | 可选 |

### 3.2 详细接口规范

#### 3.2.1 获取价值投资推荐

```http
GET /api/stocks/recommend?market=a-share&limit=20&min_roe=15
```

**Query Parameters:**
- `market` (string, required): 市场类型 `a-share` | `us`
- `limit` (integer, optional): 返回数量，默认 20，最大 100
- `min_roe` (decimal, optional): 最小 ROE 筛选，默认 10
- `industry` (string, optional): 行业筛选

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "stock_code": "600519.SH",
      "name": "贵州茅台",
      "market": "A",
      "industry": "白酒",
      "market_cap": 2150000000000,
      "latest_roe": 0.2856,
      "latest_pe": 32.5,
      "gross_margin": 0.9123,
      "recommendation_score": 95,
      "recommendation_reason": "高ROE、稳定增长、护城河深厚"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "limit": 20,
    "cached": true
  }
}
```

#### 3.2.2 获取财报数据（时间线）

```http
GET /api/financials/600519.SH?years=5&report_type=annual
```

**Path Parameters:**
- `code` (string, required): 股票代码

**Query Parameters:**
- `years` (integer, optional): 历史年数，默认 5
- `report_type` (string, optional): `annual` | `Q1` | `Q2` | `Q3`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "stock_code": "600519.SH",
    "name": "贵州茅台",
    "timeline": [
      {
        "report_date": "2025-12-31",
        "report_type": "annual",
        "revenue": 127500000000,
        "revenue_yoy": 0.152,
        "net_profit": 62500000000,
        "net_profit_yoy": 0.185,
        "roe": 0.2856,
        "gross_margin": 0.9123,
        "eps": 498.5,
        "operating_cash_flow": 65000000000
      }
    ],
    "chart_data": {
      "dates": ["2021-12-31", "2022-12-31", ...],
      "revenues": [109000000000, 114000000000, ...],
      "net_profits": [52000000000, 54000000000, ...]
    }
  }
}
```

#### 3.2.3 获取股东信息

```http
GET /api/shareholders/600519.SH?report_date=2025-12-31
```

**Path Parameters:**
- `code` (string, required): 股票代码

**Query Parameters:**
- `report_date` (date, optional): 指定报告期，默认最新

**Response 200:**
```json
{
  "success": true,
  "data": {
    "stock_code": "600519.SH",
    "report_date": "2025-12-31",
    "top_10_shareholders": [
      {
        "rank": 1,
        "holder_name": "中国贵州茅台酒厂(集团)有限责任公司",
        "hold_amount": 6780000000,
        "hold_ratio": 54.06,
        "holder_type": "国有法人"
      }
    ],
    "institutional_holders": [
      {
        "institution_name": "香港中央结算有限公司",
        "hold_amount": 1250000000,
        "hold_ratio": 9.96,
        "institution_type": "外资"
      }
    ]
  }
}
```

### 3.3 错误响应

```json
{
  "success": false,
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "股票代码不存在",
    "details": "600520.SH 未在数据库中找到"
  }
}
```

**错误码定义:**
- `STOCK_NOT_FOUND`: 股票不存在
- `INVALID_MARKET`: 无效的市场参数
- `DATA_UNAVAILABLE`: 数据暂不可用
- `RATE_LIMIT_EXCEEDED`: API 频率限制

---

## 4. 技术决策文档

### 4.1 为什么选择 FastAPI 而非 Django？

| 维度 | FastAPI | Django | 决策 |
|------|---------|--------|------|
| **性能** | 异步支持，高性能 | 同步为主，性能中等 | ✅ FastAPI |
| **开发速度** | 类型提示，自动文档 | 成熟生态，快速开发 | 平局 |
| **API 优先** | 原生 REST/GraphQL | 需要 DRF 扩展 | ✅ FastAPI |
| **学习曲线** | 简单直观 | 较陡峭 | ✅ FastAPI |
| **类型安全** | Pydantic 强类型 | 弱类型 | ✅ FastAPI |
| **生态系统** | 中等 | 非常成熟 | ⚠️ Django |

**结论：选择 FastAPI**

**理由：**
1. **性能优势**：异步支持更适合 I/O 密集型场景（多 API 调用）
2. **类型安全**：Pydantic 模型提供编译时类型检查，减少运行时错误
3. **自动文档**：OpenAPI/Swagger UI 自动生成，降低前端对接成本
4. **现代化**：Python 3.10+ 类型提示，代码更易维护
5. **轻量级**：不需要 Django 的完整 MVC 框架，API 项目更灵活

### 4.2 为什么选择 PostgreSQL + Neo4j？

#### PostgreSQL（MVP 必需）

**优势：**
- **成熟稳定**：40+ 年历史，ACID 事务保证
- **JSON 支持**：JSONB 类型存储半结构化数据
- **性能优异**：复杂查询、JOIN 性能出色
- **扩展性**：支持分区表、全文搜索、地理信息
- **生态丰富**：ORM（SQLAlchemy）、迁移工具成熟

**适用场景：**
- 股票基础信息存储
- 财报结构化数据
- 股价时序数据（分区表）
- 用户数据、配置数据

#### Neo4j（v1.5 引入）

**优势：**
- **图查询**：Cypher 语言原生支持关系查询
- **性能**：图遍历比关系型 JOIN 快 1000x+
- **可视化**：与前端 G6 完美配合

**适用场景（v1.5）：**
- 股票-行业关系图谱
- 股东-公司关联网络
- 产业链上下游关系
- 供应链分析

**架构演进路径：**
```
v1.0 (MVP): PostgreSQL 单数据库
v1.5 (知识图谱): PostgreSQL + Neo4j 双写
v2.0 (智能分析): + MongoDB(新闻) + Milvus(向量)
```

### 4.3 如何处理 Tushare API 频率限制？

#### Tushare 限制规则
- **免费版**：每分钟 200 次
- **付费版**：每分钟 2000 次
- **批量接口**：单次最多 5000 条

#### 应对策略

**1. 分层缓存策略**

```python
# 缓存层级
CACHE_LAYERS = {
    "L1_memory": TTL=60,      # 内存缓存，1分钟
    "L2_redis": TTL=3600,     # Redis 缓存，1小时
    "L3_db": TTL=86400        # 数据库缓存，1天
}

# 缓存键规则
def get_cache_key(endpoint: str, params: dict) -> str:
    return f"tushare:{endpoint}:{hashlib.md5(str(params).encode()).hexdigest()}"
```

**2. 请求队列 + 限流器**

```python
from ratelimit import limits, sleep_and_retry

class TushareClient:
    def __init__(self, api_key: str):
        self.client = ts.pro_api(api_key)
        self.request_queue = Queue()
        
    @sleep_and_retry
    @limits(calls=180, period=60)  # 留 10% 余量
    def _request_with_limit(self, func, **kwargs):
        return func(**kwargs)
    
    async def get_stock_basic(self, retry=3):
        for i in range(retry):
            try:
                return self._request_with_limit(
                    self.client.stock_basic,
                    exchange='',
                    list_status='L'
                )
            except Exception as e:
                if i == retry - 1:
                    raise
                await asyncio.sleep(2 ** i)  # 指数退避
```

**3. 批量预加载 + 增量更新**

```python
# Celery 定时任务
@celery.task
def daily_data_sync():
    """每日凌晨 2 点执行全量同步"""
    stocks = get_all_stock_codes()
    batch_size = 100
    
    for i in range(0, len(stocks), batch_size):
        batch = stocks[i:i+batch_size]
        sync_stock_data.delay(batch)
        time.sleep(1)  # 批次间间隔

@celery.task
def sync_stock_data(stock_codes: list):
    """异步同步单批次数据"""
    for code in stock_codes:
        data = tushare_client.get_daily(code)
        save_to_db(data)
```

**4. 降级策略**

```python
class DataFetcher:
    async def get_financials(self, stock_code: str):
        # 1. 优先从缓存读取
        cached = await redis.get(f"fin:{stock_code}")
        if cached:
            return json.loads(cached)
        
        # 2. 尝试 Tushare API
        try:
            data = await self._fetch_from_tushare(stock_code)
            await redis.setex(f"fin:{stock_code}", 3600, json.dumps(data))
            return data
        except RateLimitError:
            # 3. 降级到数据库历史数据
            return await self._fetch_from_db(stock_code)
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            raise
```

**5. 监控与告警**

```python
# Prometheus 指标
tushare_requests_total = Counter('tushare_requests_total', 'Total Tushare API requests')
tushare_requests_failed = Counter('tushare_requests_failed', 'Failed Tushare API requests')
tushare_rate_limit_hits = Counter('tushare_rate_limit_hits', 'Rate limit hits')

# 告警规则
ALERT_RULES = {
    "rate_limit_exceeded": {
        "condition": "tushare_rate_limit_hits > 10 in 5min",
        "action": "send_alert_to_slack"
    }
}
```

---

## 5. 系统部署架构

### 5.1 容器化部署（Docker Compose）

```yaml
# docker-compose.yml (MVP)
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: valuegraph
      POSTGRES_USER: vg_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://vg_user:${DB_PASSWORD}@postgres:5432/valuegraph
      REDIS_URL: redis://redis:6379
      TUSHARE_TOKEN: ${TUSHARE_TOKEN}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    
  celery-worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://vg_user:${DB_PASSWORD}@postgres:5432/valuegraph
      REDIS_URL: redis://redis:6379
      TUSHARE_TOKEN: ${TUSHARE_TOKEN}
    depends_on:
      - redis
      - postgres

volumes:
  pg_data:
```

### 5.2 生产环境架构（v1.5+）

```mermaid
graph LR
    LB[Load Balancer<br/>Nginx] --> API1[FastAPI Pod 1]
    LB --> API2[FastAPI Pod 2]
    
    API1 --> PG_M[PostgreSQL Master]
    API2 --> PG_M
    
    PG_M -.->|Replication| PG_S[PostgreSQL Slave]
    
    API1 --> Redis_Cluster[Redis Cluster]
    API2 --> Redis_Cluster
    
    API1 --> Neo4j
    API2 --> Neo4j
    
    style LB fill:#00BCD4,stroke:#0097A7,color:#fff
    style PG_M fill:#4CAF50,stroke:#388E3C,color:#fff
```

---

## 6. 性能指标与监控

### 6.1 关键指标

| 指标 | 目标值 | 监控方式 |
|------|--------|----------|
| API 响应时间 | P95 < 200ms | Prometheus + Grafana |
| 数据库查询 | P95 < 50ms | PostgreSQL Exporter |
| 缓存命中率 | > 80% | Redis Exporter |
| Celery 任务成功率 | > 99% | Flower |
| Tushare API 失败率 | < 1% | 自定义指标 |

### 6.2 日志策略

```python
# 结构化日志
import structlog

logger = structlog.get_logger()

logger.info(
    "api_request",
    endpoint="/api/stocks/recommend",
    market="a-share",
    duration_ms=156,
    cached=True,
    user_ip="192.168.1.100"
)
```

---

## 7. 安全性设计

### 7.1 API 安全
- **Rate Limiting**: 100 req/min per IP
- **CORS**: 白名单域名
- **Input Validation**: Pydantic 严格校验
- **SQL Injection**: SQLAlchemy 参数化查询

### 7.2 数据安全
- **敏感信息**: 环境变量 + Vault
- **数据库**: TLS 加密连接
- **备份**: 每日自动备份到 S3

---

## 8. 开发路线图

### Phase 1: MVP (Week 1-8)
- ✅ PostgreSQL 数据库搭建
- ✅ FastAPI 核心接口开发
- ✅ Tushare 数据采集
- ✅ Next.js 前端框架
- ✅ 基础推荐算法

### Phase 2: 知识图谱 (Week 9-16)
- ⏳ Neo4j 集成
- ⏳ G6 图谱可视化
- ⏳ 产业链分析

### Phase 3: 智能分析 (Week 17-24)
- 📋 MongoDB 新闻存储
- 📋 Milvus 向量搜索
- 📋 AI 推荐引擎

---

## 9. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Tushare API 不稳定 | 高 | 中 | 多数据源备份 + 缓存降级 |
| 数据库性能瓶颈 | 中 | 低 | 分区表 + 读写分离 |
| 前端渲染性能 | 中 | 中 | 虚拟滚动 + 懒加载 |
| 第三方库漏洞 | 高 | 低 | 定期安全扫描 + 依赖更新 |

---

## 附录：技术栈版本清单

| 组件 | 版本 | 备注 |
|------|------|------|
| Python | 3.11+ | 类型提示优化 |
| FastAPI | 0.100+ | 异步支持 |
| PostgreSQL | 15+ | 性能提升 |
| Redis | 7+ | JSON 支持 |
| Next.js | 14+ | App Router |
| React | 18+ | Server Components |
| TypeScript | 5.0+ | 类型安全 |

---

**文档维护**: 本架构设计将随项目演进持续更新。如有疑问或建议，请联系 @architect。
