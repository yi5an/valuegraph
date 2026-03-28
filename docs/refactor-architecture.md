# ValueGraph 重构架构方案（MVP）

> **版本**：v2.0 (MVP 重构版)  
> **日期**：2026-03-24  
> **作者**：Architect  
> **状态**：最终方案确认  

---

## 📋 执行摘要

### 核心决策

| 决策项 | 结论 | 理由 |
|--------|------|------|
| **数据库架构** | PostgreSQL 单库 | MVP 阶段数据规模小，单库足够，降低运维复杂度 |
| **图数据库** | ❌ 暂不引入 Neo4j | v1.5 再引入，MVP 用 PostgreSQL 存储关系数据 |
| **向量数据库** | ❌ 暂不引入 Milvus | v2.0 再引入智能问答功能 |
| **文档数据库** | ❌ 暂不引入 MongoDB | v1.5 再引入新闻聚合功能 |

### MVP 功能范围

```
✅ 模块1：多市场价值投资推荐（A股 + 美股）
✅ 模块2：财报深度分析（时间线展示）
✅ 模块6：持股信息查询（十大股东 + 机构持仓）

❌ 模块3：新闻资讯聚合（v1.5）
❌ 模块4：知识图谱构建（v1.5）
❌ 模块5：图谱智能挖掘（v2.0）
```

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────┐
│         前端展示层 (Next.js 14)                  │
│  ┌───────────┬───────────┬───────────┐          │
│  │ 价值推荐   │ 财报分析   │ 持股查询   │          │
│  │ (ECharts) │ (Timeline)│ (Table)   │          │
│  └───────────┴───────────┴───────────┘          │
└─────────────────────────────────────────────────┘
                    ↓ REST API
┌─────────────────────────────────────────────────┐
│         业务逻辑层 (FastAPI)                     │
│  ┌────────────────────────────────────────┐     │
│  │ 推荐引擎 │ 财报解析 │ 持股分析 │ 缓存层 │     │
│  └────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         数据存储层                               │
│  ┌──────────┬──────────┐                        │
│  │PostgreSQL│  Redis   │                        │
│  │(核心数据) │ (缓存)   │                        │
│  └──────────┴──────────┘                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         数据采集层                               │
│  ┌──────────┬──────────┬──────────┐             │
│  │ Tushare  │  Yahoo   │  SEC     │             │
│  │  (A股)   │ Finance  │  EDGAR   │             │
│  └──────────┴──────────┴──────────┘             │
│  Celery 定时任务 + 限流器                         │
└─────────────────────────────────────────────────┘
```

---

## 🗂️ 项目目录结构

### 后端（FastAPI）

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理（环境变量）
│   ├── database.py                # 数据库连接（SQLAlchemy）
│   │
│   ├── models/                    # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── stock.py               # 股票基础信息
│   │   ├── financial.py           # 财报数据
│   │   ├── price.py               # 股价数据
│   │   └── shareholder.py         # 股东信息
│   │
│   ├── schemas/                   # Pydantic 数据模型（API 输入输出）
│   │   ├── __init__.py
│   │   ├── stock.py               # 股票相关 Schema
│   │   ├── financial.py           # 财报相关 Schema
│   │   └── shareholder.py         # 股东相关 Schema
│   │
│   ├── api/                       # API 路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── stocks.py          # 股票推荐接口
│   │   │   ├── financials.py      # 财报查询接口
│   │   │   ├── shareholders.py    # 股东信息接口
│   │   │   └── prices.py          # 股价历史接口
│   │   └── deps.py                # 依赖注入（DB Session、Redis）
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── recommendation.py      # 推荐算法
│   │   ├── financial_analysis.py  # 财报分析
│   │   ├── shareholder_service.py # 股东服务
│   │   └── cache.py               # 缓存服务
│   │
│   ├── collectors/                # 数据采集器
│   │   ├── __init__.py
│   │   ├── tushare_client.py      # Tushare API 封装
│   │   ├── yahoo_client.py        # Yahoo Finance API 封装
│   │   ├── sec_client.py          # SEC EDGAR API 封装
│   │   └── rate_limiter.py        # 限流器
│   │
│   ├── tasks/                     # Celery 异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery 配置
│   │   ├── stock_sync.py          # 股票数据同步
│   │   ├── financial_sync.py      # 财报数据同步
│   │   └── shareholder_sync.py    # 股东数据同步
│   │
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── logger.py              # 日志配置
│       └── exceptions.py          # 自定义异常
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py                # Pytest 配置
│   ├── test_api/                  # API 测试
│   └── test_services/             # 服务层测试
│
├── alembic/                       # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── requirements.txt               # Python 依赖
├── Dockerfile                     # Docker 镜像
├── docker-compose.yml             # 本地开发环境
└── .env.example                   # 环境变量模板
```

### 前端（Next.js）

```
frontend/
├── src/
│   ├── app/                       # Next.js 14 App Router
│   │   ├── layout.tsx             # 根布局
│   │   ├── page.tsx               # 首页
│   │   ├── globals.css            # 全局样式
│   │   │
│   │   ├── recommend/             # 价值推荐页面
│   │   │   └── page.tsx
│   │   │
│   │   ├── financials/            # 财报分析页面
│   │   │   └── [code]/
│   │   │       └── page.tsx
│   │   │
│   │   └── shareholders/          # 持股查询页面
│   │       └── [code]/
│   │           └── page.tsx
│   │
│   ├── components/                # React 组件
│   │   ├── layout/
│   │   │   ├── Header.tsx         # 头部导航
│   │   │   ├── Sidebar.tsx        # 侧边栏
│   │   │   └── Footer.tsx         # 底部
│   │   │
│   │   ├── recommend/
│   │   │   ├── StockCard.tsx      # 股票卡片
│   │   │   ├── FilterPanel.tsx    # 筛选面板
│   │   │   └── StockTable.tsx     # 股票列表表格
│   │   │
│   │   ├── financials/
│   │   │   ├── TimelineChart.tsx  # 时间线图表
│   │   │   ├── MetricCard.tsx     # 指标卡片
│   │   │   └── RadarChart.tsx     # 雷达图（财务健康度）
│   │   │
│   │   ├── shareholders/
│   │   │   ├── HolderTable.tsx    # 股东列表
│   │   │   └── HolderPieChart.tsx # 持股分布饼图
│   │   │
│   │   └── common/
│   │       ├── Loading.tsx        # 加载状态
│   │       ├── Error.tsx          # 错误提示
│   │       └── MarketSelector.tsx # 市场切换
│   │
│   ├── lib/                       # 工具库
│   │   ├── api.ts                 # API 客户端（Axios）
│   │   ├── utils.ts               # 工具函数
│   │   └── constants.ts           # 常量定义
│   │
│   ├── hooks/                     # 自定义 Hooks
│   │   ├── useStocks.ts           # 股票数据 Hook
│   │   ├── useFinancials.ts       # 财报数据 Hook
│   │   └── useShareholders.ts     # 股东数据 Hook
│   │
│   ├── types/                     # TypeScript 类型定义
│   │   ├── stock.ts
│   │   ├── financial.ts
│   │   └── shareholder.ts
│   │
│   └── styles/                    # 样式文件
│       └── theme.ts               # Ant Design 主题配置
│
├── public/                        # 静态资源
│   └── favicon.ico
│
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
└── .env.local
```

---

## 🧩 核心模块划分

### 后端模块

| 模块 | 职责 | 核心类/函数 |
|------|------|------------|
| **推荐引擎** | 价值投资筛选与排序 | `RecommendationService.filter_stocks()`<br/>`RecommendationService.calculate_score()` |
| **财报分析** | 财务数据计算与趋势分析 | `FinancialService.get_timeline()`<br/>`FinancialService.analyze_trend()` |
| **持股服务** | 股东信息查询与变化监控 | `ShareholderService.get_top_holders()`<br/>`ShareholderService.get_changes()` |
| **数据采集** | 第三方 API 调用与限流 | `TushareClient`<br/>`RateLimiter` |
| **缓存层** | Redis 缓存管理 | `CacheService.get()`<br/>`CacheService.set()` |

### 前端模块

| 模块 | 页面/组件 | 核心功能 |
|------|----------|---------|
| **价值推荐** | `/recommend` | 市场切换、筛选器、股票列表、详情跳转 |
| **财报分析** | `/financials/[code]` | 时间线图表、财务指标、趋势分析 |
| **持股查询** | `/shareholders/[code]` | 十大股东、机构持仓、持股变化 |
| **公共组件** | Layout、Header | 导航、市场切换、全局样式 |

---

## 🛣️ API 路由设计

### API 端点总览

```
/api/v1/stocks/recommend          # 获取价值推荐列表
/api/v1/stocks/:code              # 获取股票详情
/api/v1/financials/:code          # 获取财报时间线
/api/v1/shareholders/:code        # 获取股东信息
/api/v1/prices/:code              # 获取股价历史
```

### 详细接口规范

#### 1. 价值投资推荐

```http
GET /api/v1/stocks/recommend
```

**Query Parameters:**
```typescript
{
  market: 'a-share' | 'us',      // 必填
  limit?: number,                 // 默认 20，最大 100
  min_roe?: number,               // 默认 15
  max_debt_ratio?: number,        // 默认 50
  industry?: string               // 可选
}
```

**Response:**
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
      "debt_ratio": 0.25,
      "recommendation_score": 95,
      "recommendation_reason": "高ROE、稳定增长、护城河深厚"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "limit": 20,
    "filters": {
      "market": "a-share",
      "min_roe": 15
    }
  }
}
```

#### 2. 财报时间线

```http
GET /api/v1/financials/:code
```

**Path Parameters:**
- `code`: 股票代码（如 `600519.SH`）

**Query Parameters:**
```typescript
{
  years?: number,          // 默认 5 年
  report_type?: 'annual' | 'Q1' | 'Q2' | 'Q3'
}
```

**Response:**
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
        "debt_ratio": 0.25,
        "operating_cash_flow": 65000000000,
        "eps": 498.5,
        "bvps": 1745.2
      }
    ],
    "chart_data": {
      "dates": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"],
      "revenues": [109000000000, 114000000000, 119000000000, 122000000000, 127500000000],
      "net_profits": [52000000000, 54000000000, 57000000000, 59000000000, 62500000000],
      "roes": [0.2912, 0.2845, 0.2801, 0.2823, 0.2856]
    },
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

#### 3. 股东信息

```http
GET /api/v1/shareholders/:code
```

**Path Parameters:**
- `code`: 股票代码

**Query Parameters:**
```typescript
{
  report_date?: string,    // 默认最新，格式：YYYY-MM-DD
  holder_type?: 'top10' | 'institution' | 'all'  // 默认 all
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stock_code": "600519.SH",
    "name": "贵州茅台",
    "report_date": "2025-12-31",
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
    "institutional_holders": [
      {
        "institution_name": "香港中央结算有限公司",
        "hold_amount": 1250000000,
        "hold_ratio": 9.96,
        "institution_type": "外资",
        "change": "+0.5%"
      }
    ],
    "holder_distribution": {
      "institutional": 45.2,
      "individual": 35.8,
      "foreign": 19.0
    }
  }
}
```

#### 4. 股价历史

```http
GET /api/v1/prices/:code
```

**Query Parameters:**
```typescript
{
  start_date?: string,     // 默认 1 年前
  end_date?: string,       // 默认今天
  limit?: number           // 默认 250（约 1 年交易日）
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stock_code": "600519.SH",
    "name": "贵州茅台",
    "prices": [
      {
        "trade_date": "2025-03-24",
        "open": 1850.50,
        "high": 1865.20,
        "low": 1848.00,
        "close": 1862.00,
        "volume": 3250000,
        "change_pct": 0.62
      }
    ],
    "statistics": {
      "latest_price": 1862.00,
      "year_high": 1920.50,
      "year_low": 1650.00,
      "avg_volume": 3100000
    }
  }
}
```

---

## 🗄️ 数据库表设计（精简版）

### 表结构

#### 1. stocks（股票基础信息）

```sql
CREATE TABLE stocks (
    stock_code VARCHAR(20) PRIMARY KEY,        -- 股票代码（如 600519.SH）
    market VARCHAR(10) NOT NULL,                -- 市场：A, US, HK
    name VARCHAR(100) NOT NULL,                 -- 股票名称
    industry VARCHAR(50),                       -- 所属行业
    sector VARCHAR(50),                         -- 所属板块
    market_cap DECIMAL(18, 2),                  -- 总市值
    listed_date DATE,                           -- 上市日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_market CHECK (market IN ('A', 'US', 'HK', 'IN'))
);

CREATE INDEX idx_stocks_market ON stocks(market);
CREATE INDEX idx_stocks_industry ON stocks(industry);
```

#### 2. financials（财报数据）

```sql
CREATE TABLE financials (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    report_date DATE NOT NULL,                  -- 报告期
    report_type VARCHAR(20) NOT NULL,           -- annual, Q1, Q2, Q3
    
    -- 核心财务指标
    revenue DECIMAL(18, 2),                     -- 营业收入
    net_profit DECIMAL(18, 2),                  -- 净利润
    total_assets DECIMAL(18, 2),                -- 总资产
    total_liabilities DECIMAL(18, 2),           -- 总负债
    operating_cash_flow DECIMAL(18, 2),         -- 经营现金流
    
    -- 计算指标
    roe DECIMAL(8, 4),                          -- ROE
    gross_margin DECIMAL(8, 4),                 -- 毛利率
    debt_ratio DECIMAL(8, 4),                   -- 负债率
    eps DECIMAL(10, 4),                         -- 每股收益
    bvps DECIMAL(10, 4),                        -- 每股净资产
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_code, report_date, report_type)
);

CREATE INDEX idx_financials_code_date ON financials(stock_code, report_date DESC);
```

#### 3. stock_prices（股价数据）

```sql
CREATE TABLE stock_prices (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    trade_date DATE NOT NULL,                   -- 交易日期
    
    open DECIMAL(12, 4),                        -- 开盘价
    high DECIMAL(12, 4),                        -- 最高价
    low DECIMAL(12, 4),                         -- 最低价
    close DECIMAL(12, 4),                       -- 收盘价
    volume BIGINT,                              -- 成交量
    amount DECIMAL(18, 2),                      -- 成交额
    change_pct DECIMAL(8, 4),                   -- 涨跌幅
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_code, trade_date)
);

CREATE INDEX idx_prices_code_date ON stock_prices(stock_code, trade_date DESC);
```

#### 4. shareholders（十大股东）

```sql
CREATE TABLE shareholders (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    report_date DATE NOT NULL,                  -- 报告期
    
    rank INTEGER NOT NULL,                      -- 排名
    holder_name VARCHAR(200) NOT NULL,          -- 股东名称
    hold_amount BIGINT,                         -- 持股数量
    hold_ratio DECIMAL(8, 4),                   -- 持股比例
    holder_type VARCHAR(50),                    -- 股东类型
    change VARCHAR(20),                         -- 变化情况（新增/不变/减持）
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shareholders_code_date ON shareholders(stock_code, report_date DESC);
CREATE INDEX idx_shareholders_holder ON shareholders(holder_name);
```

#### 5. institutional_holders（机构持仓）

```sql
CREATE TABLE institutional_holders (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL REFERENCES stocks(stock_code),
    report_date DATE NOT NULL,                  -- 报告期
    
    institution_name VARCHAR(200) NOT NULL,     -- 机构名称
    institution_type VARCHAR(50),               -- 机构类型（基金/券商/外资等）
    hold_amount BIGINT,                         -- 持股数量
    hold_ratio DECIMAL(8, 4),                   -- 持股比例
    change_ratio DECIMAL(8, 4),                 -- 变化比例
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_institutional_code_date ON institutional_holders(stock_code, report_date DESC);
CREATE INDEX idx_institutional_name ON institutional_holders(institution_name);
```

### 数据库关系图

```
stocks (1) ──────── (N) financials
   │
   ├── (N) stock_prices
   │
   ├── (N) shareholders
   │
   └── (N) institutional_holders
```

---

## 🔧 技术栈确认

### 后端技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 运行环境 |
| **FastAPI** | 0.100+ | Web 框架 |
| **SQLAlchemy** | 2.0+ | ORM |
| **Alembic** | 1.12+ | 数据库迁移 |
| **Pydantic** | 2.0+ | 数据验证 |
| **PostgreSQL** | 15+ | 关系数据库 |
| **Redis** | 7+ | 缓存 + 任务队列 |
| **Celery** | 5.3+ | 异步任务 |
| **Tushare** | 1.3+ | A股数据源 |
| **yfinance** | 0.2+ | 美股数据源 |

### 前端技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| **Node.js** | 18+ | 运行环境 |
| **Next.js** | 14+ | 前端框架 |
| **React** | 18+ | UI 库 |
| **TypeScript** | 5.0+ | 类型安全 |
| **Ant Design** | 5.x | UI 组件库 |
| **TailwindCSS** | 3.x | 样式框架 |
| **ECharts** | 5.x | 图表可视化 |
| **Zustand** | 4.x | 状态管理 |
| **Axios** | 1.x | HTTP 客户端 |

---

## 📊 性能指标

### API 性能目标

| 接口 | 目标响应时间 | 缓存策略 |
|------|-------------|---------|
| `/api/v1/stocks/recommend` | P95 < 300ms | Redis 1 小时 |
| `/api/v1/financials/:code` | P95 < 200ms | Redis 6 小时 |
| `/api/v1/shareholders/:code` | P95 < 200ms | Redis 6 小时 |
| `/api/v1/prices/:code` | P95 < 150ms | Redis 1 小时 |

### 数据库优化

- **索引策略**：所有查询字段建立复合索引
- **分区表**：`stock_prices` 按年份分区（数据量大时）
- **连接池**：最大连接数 20，最小 5
- **查询优化**：避免 N+1 查询，使用 JOIN 预加载

---

## 🚀 开发计划（8 周）

### Week 1-2: 基础架构搭建

- [x] PostgreSQL 数据库初始化
- [x] FastAPI 项目脚手架
- [x] SQLAlchemy 模型定义
- [x] Alembic 迁移脚本
- [x] Redis 连接配置

### Week 3-4: 数据采集层

- [x] Tushare API 客户端封装
- [x] Yahoo Finance API 客户端
- [x] 限流器实现
- [x] Celery 定时任务配置
- [x] 数据同步脚本

### Week 5-6: 业务逻辑层

- [x] 推荐算法实现
- [x] 财报分析服务
- [x] 股东信息服务
- [x] 缓存层集成
- [x] 单元测试

### Week 7-8: 前端开发 + 集成

- [x] Next.js 项目初始化
- [x] 价值推荐页面
- [x] 财报分析页面
- [x] 持股查询页面
- [x] 前后端联调
- [x] 部署上线

---

## ⚠️ 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **Tushare API 不稳定** | 高 | 中 | 多数据源备份（东方财富爬虫）+ 缓存降级 |
| **数据库性能瓶颈** | 中 | 低 | 分区表 + 索引优化 + 读写分离（v1.5） |
| **前端渲染性能** | 中 | 中 | 虚拟滚动 + 懒加载 + 分页 |
| **数据同步延迟** | 中 | 中 | 定时任务 + 增量更新 + 监控告警 |

---

## 📝 决策记录

### ADR-001: 为什么 MVP 不用 Neo4j？

**背景**：PRD 中提到知识图谱需要 Neo4j，但 MVP 阶段数据规模小。

**决策**：MVP 阶段只用 PostgreSQL，v1.5 再引入 Neo4j。

**理由**：
1. **数据规模**：MVP 只有 5000 只股票，关系数据用 PostgreSQL 足够
2. **运维成本**：Neo4j 需要单独部署和维护，增加复杂度
3. **开发时间**：MVP 需要快速验证，图谱功能可延后
4. **性能**：PostgreSQL 的 JSONB 类型可存储简单关系，查询性能足够

**后果**：
- ✅ 降低初期运维复杂度
- ✅ 缩短开发周期
- ⚠️ v1.5 需要数据迁移（PostgreSQL → Neo4j）

### ADR-002: 为什么选择 Celery 而非 RQ？

**背景**：需要异步任务调度，Celery 和 RQ 都是选择。

**决策**：选择 Celery。

**理由**：
1. **功能丰富**：支持定时任务、任务重试、任务优先级
2. **生态成熟**：与 FastAPI、SQLAlchemy 集成良好
3. **性能**：支持多进程、协程，性能优于 RQ
4. **监控**：Flower 提供可视化监控界面

### ADR-003: 前端为什么选择 Next.js 而非 Vite SPA？

**背景**：前端框架选择，Next.js 和 Vite SPA 都是选择。

**决策**：选择 Next.js 14（App Router）。

**理由**：
1. **SSR 支持**：首屏加载快，SEO 友好
2. **API Routes**：可以做 BFF（Backend for Frontend）
3. **生态成熟**：与 React 18、TypeScript 集成良好
4. **性能**：自动代码分割、图片优化
5. **部署简单**：Vercel 一键部署

---

## 📚 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Next.js 14 文档](https://nextjs.org/docs)
- [PostgreSQL 15 文档](https://www.postgresql.org/docs/15/index.html)
- [Tushare Pro API](https://tushare.pro/document/2)
- [Ant Design 5.x](https://ant.design/docs/react/introduce-cn)

---

**文档维护**：本架构方案为 MVP 最终版本，后续迭代将在 v1.5/v2.0 版本更新。  
**下次评审**：MVP 上线后（预计 8 周后）  
**负责人**：@architect
