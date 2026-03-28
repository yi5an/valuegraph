# ValueGraph API 接口规范 v1.0

> **版本**: v1.0  
> **基础路径**: `/api/v1`  
> **协议**: REST over HTTPS  
> **数据格式**: JSON  
> **创建日期**: 2026-03-25  
> **作者**: Architect  

---

## 1. 概述

### 1.1 API 设计原则

- **RESTful 风格**: 资源导向，语义化 URL
- **统一响应格式**: 标准化的成功/错误响应结构
- **版本控制**: URL 路径版本 (`/api/v1/`)
- **分页支持**: 大数据集支持分页
- **多市场支持**: A股 (Ashare)、美股 (Finnhub)、港股 (Finnhub)

### 1.2 基础信息

| 项目 | 值 |
|------|-----|
| 基础 URL | `http://localhost:8000/api/v1` |
| 文档 | `/docs` (Swagger UI) |
| OpenAPI | `/openapi.json` |
| 认证 | Bearer Token (可选) |

### 1.3 通用响应格式

#### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-25T10:30:00Z",
    "cached": true,
    "source": "database"
  }
}
```

#### 错误响应

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

### 1.4 错误码定义

| 错误码 | HTTP 状态码 | 描述 |
|--------|------------|------|
| `STOCK_NOT_FOUND` | 404 | 股票代码不存在 |
| `INVALID_MARKET` | 400 | 无效的市场参数 |
| `INVALID_PARAMETER` | 400 | 参数校验失败 |
| `DATA_UNAVAILABLE` | 503 | 数据暂不可用 |
| `RATE_LIMIT_EXCEEDED` | 429 | API 频率限制 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## 2. 价值推荐 API

### 2.1 获取价值投资推荐列表

基于价值投资理念筛选优质股票。

#### 请求

```http
GET /api/v1/stocks/recommend
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `market` | string | 否 | `A` | 市场类型: `A` (A股), `US` (美股), `HK` (港股) |
| `limit` | integer | 否 | `20` | 返回数量 (1-100) |
| `min_roe` | number | 否 | `15.0` | 最低 ROE (%) |
| `max_debt_ratio` | number | 否 | `50.0` | 最高负债率 (%) |
| `min_market_cap` | number | 否 | - | 最低市值 (亿元) |
| `industry` | string | 否 | - | 行业筛选 |
| `sort_by` | string | 否 | `score` | 排序字段: `score`, `roe`, `pe` |

#### 响应

```json
{
  "success": true,
  "data": [
    {
      "stock_code": "600519",
      "name": "贵州茅台",
      "market": "A",
      "industry": "白酒",
      "sector": "消费品",
      "market_cap": 2150000000000,
      "latest_roe": 28.56,
      "latest_pe": 32.5,
      "latest_pb": 9.3,
      "debt_ratio": 25.3,
      "gross_margin": 91.23,
      "recommendation_score": 95,
      "recommendation_reason": "高ROE、低负债、估值合理"
    },
    {
      "stock_code": "000858",
      "name": "五粮液",
      "market": "A",
      "industry": "白酒",
      "sector": "消费品",
      "market_cap": 580000000000,
      "latest_roe": 25.12,
      "latest_pe": 22.8,
      "latest_pb": 5.7,
      "debt_ratio": 20.5,
      "gross_margin": 75.8,
      "recommendation_score": 92,
      "recommendation_reason": "高ROE、低负债、估值合理"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "limit": 20,
    "has_more": true,
    "filters": {
      "market": "A",
      "min_roe": 15.0,
      "max_debt_ratio": 50.0,
      "industry": null
    },
    "cached": true,
    "cache_ttl": 3600
  }
}
```

#### cURL 示例

```bash
# 基础查询
curl "http://localhost:8000/api/v1/stocks/recommend?market=A&min_roe=20&limit=10"

# 行业筛选
curl "http://localhost:8000/api/v1/stocks/recommend?market=A&industry=白酒&limit=5"

# 美股推荐
curl "http://localhost:8000/api/v1/stocks/recommend?market=US&min_roe=15&limit=10"
```

---

## 3. 财报分析 API

### 3.1 获取财报时间线

获取股票的历史财报数据，支持三大报表核心指标。

#### 请求

```http
GET /api/v1/financials/{stock_code}
```

**Path Parameters:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `stock_code` | string | 是 | 股票代码 (如 `600519`, `AAPL`) |

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `years` | integer | 否 | `5` | 历史年数 (1-10) |
| `report_type` | string | 否 | `annual` | 报告类型: `annual`, `Q1`, `Q2`, `Q3` |
| `market` | string | 否 | `auto` | 市场类型: `A`, `US`, `HK`, `auto` (自动识别) |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "name": "贵州茅台",
    "market": "A",
    "currency": "CNY",
    "timeline": [
      {
        "report_date": "2025-12-31",
        "report_type": "annual",
        "fiscal_year": 2025,
        "revenue": 127500000000,
        "revenue_yoy": 15.2,
        "net_profit": 62500000000,
        "net_profit_yoy": 18.5,
        "gross_profit": 116200000000,
        "gross_margin": 91.14,
        "operating_profit": 72000000000,
        "operating_margin": 56.47,
        "total_assets": 285000000000,
        "total_liabilities": 72000000000,
        "shareholders_equity": 213000000000,
        "debt_ratio": 25.26,
        "roe": 29.34,
        "roa": 21.93,
        "operating_cash_flow": 65000000000,
        "free_cash_flow": 58000000000,
        "eps": 498.5,
        "bvps": 1698.5,
        "dividend_per_share": 259.1
      },
      {
        "report_date": "2024-12-31",
        "report_type": "annual",
        "fiscal_year": 2024,
        "revenue": 110700000000,
        "revenue_yoy": 12.3,
        "net_profit": 52740000000,
        "net_profit_yoy": 14.8,
        "gross_margin": 90.85,
        "debt_ratio": 24.8,
        "roe": 28.56,
        "eps": 420.3
      }
    ],
    "chart_data": {
      "dates": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"],
      "revenues": [109000000000, 114000000000, 122000000000, 110700000000, 127500000000],
      "net_profits": [52000000000, 54000000000, 61000000000, 52740000000, 62500000000],
      "roes": [31.2, 29.8, 30.5, 28.56, 29.34],
      "gross_margins": [91.5, 91.2, 91.8, 90.85, 91.14]
    },
    "health_score": {
      "overall": 92,
      "profitability": 95,
      "solvency": 90,
      "growth": 88,
      "operation": 94
    },
    "trend_analysis": {
      "revenue_trend": "up",
      "profit_trend": "up",
      "roe_trend": "stable",
      "cash_flow_trend": "healthy"
    }
  }
}
```

### 3.2 获取资产负债表

#### 请求

```http
GET /api/v1/financials/{stock_code}/balance-sheet
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `report_date` | string | 否 | 最新 | 报告期 (YYYY-MM-DD) |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "report_date": "2025-12-31",
    "balance_sheet": {
      "assets": {
        "current_assets": {
          "cash_and_equivalents": 165000000000,
          "accounts_receivable": 500000000,
          "inventory": 32000000000,
          "other_current_assets": 2500000000,
          "total_current_assets": 200000000000
        },
        "non_current_assets": {
          "property_plant_equipment": 65000000000,
          "intangible_assets": 12000000000,
          "long_term_investments": 5000000000,
          "other_non_current_assets": 3000000000,
          "total_non_current_assets": 85000000000
        },
        "total_assets": 285000000000
      },
      "liabilities": {
        "current_liabilities": {
          "accounts_payable": 8500000000,
          "short_term_debt": 2000000000,
          "deferred_revenue": 35000000000,
          "other_current_liabilities": 12000000000,
          "total_current_liabilities": 57500000000
        },
        "non_current_liabilities": {
          "long_term_debt": 5000000000,
          "deferred_tax_liabilities": 4500000000,
          "other_non_current_liabilities": 5000000000,
          "total_non_current_liabilities": 14500000000
        },
        "total_liabilities": 72000000000
      },
      "equity": {
        "common_stock": 12500000000,
        "retained_earnings": 195000000000,
        "other_equity": 5500000000,
        "total_equity": 213000000000
      },
      "debt_to_equity": 0.338,
      "current_ratio": 3.48,
      "quick_ratio": 2.92
    }
  }
}
```

### 3.3 获取利润表

#### 请求

```http
GET /api/v1/financials/{stock_code}/income-statement
```

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "report_date": "2025-12-31",
    "income_statement": {
      "revenue": 127500000000,
      "cost_of_revenue": 11300000000,
      "gross_profit": 116200000000,
      "gross_margin": 91.14,
      "operating_expenses": {
        "selling_expenses": 32000000000,
        "admin_expenses": 8500000000,
        "rd_expenses": 200000000,
        "total_operating_expenses": 40700000000
      },
      "operating_income": 75500000000,
      "operating_margin": 59.22,
      "other_income": 500000000,
      "interest_expense": 300000000,
      "pre_tax_income": 75700000000,
      "income_tax": 13200000000,
      "net_income": 62500000000,
      "net_margin": 49.02,
      "eps_basic": 498.5,
      "eps_diluted": 498.5,
      "dividend_per_share": 259.1
    }
  }
}
```

### 3.4 获取现金流量表

#### 请求

```http
GET /api/v1/financials/{stock_code}/cash-flow
```

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "report_date": "2025-12-31",
    "cash_flow": {
      "operating_activities": {
        "net_income": 62500000000,
        "depreciation_amortization": 3500000000,
        "changes_in_working_capital": -1200000000,
        "other_operating": 200000000,
        "net_cash_from_operations": 65000000000
      },
      "investing_activities": {
        "capital_expenditures": -5500000000,
        "acquisitions": 0,
        "investments_purchased": -2000000000,
        "investments_sold": 1500000000,
        "net_cash_from_investing": -6000000000
      },
      "financing_activities": {
        "debt_issued": 1000000000,
        "debt_repaid": -1500000000,
        "dividends_paid": -32500000000,
        "share_repurchases": 0,
        "net_cash_from_financing": -33000000000
      },
      "net_change_in_cash": 26000000000,
      "cash_at_beginning": 139000000000,
      "cash_at_end": 165000000000,
      "free_cash_flow": 59500000000,
      "fcf_yield": 2.77
    }
  }
}
```

---

## 4. 持股查询 API

### 4.1 获取股东信息

获取股票的股东结构和机构持股信息。

#### 请求

```http
GET /api/v1/shareholders/{stock_code}
```

**Path Parameters:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `stock_code` | string | 是 | 股票代码 |

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `report_date` | string | 否 | 最新 | 报告期 (YYYY-MM-DD) |
| `market` | string | 否 | `auto` | 市场类型 |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
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
      },
      {
        "rank": 2,
        "holder_name": "香港中央结算有限公司",
        "hold_amount": 1250000000,
        "hold_ratio": 9.96,
        "holder_type": "境外机构",
        "change": "增持"
      },
      {
        "rank": 3,
        "holder_name": "贵州省国有资本运营有限责任公司",
        "hold_amount": 560000000,
        "hold_ratio": 4.46,
        "holder_type": "国有法人",
        "change": "不变"
      }
    ],
    "institutional_holders": [
      {
        "institution_name": "易方达基金管理有限公司",
        "hold_amount": 85000000,
        "hold_ratio": 0.68,
        "institution_type": "基金",
        "change_ratio": 0.12,
        "report_date": "2025-12-31"
      },
      {
        "institution_name": "华夏基金管理有限公司",
        "hold_amount": 72000000,
        "hold_ratio": 0.57,
        "institution_type": "基金",
        "change_ratio": -0.05,
        "report_date": "2025-12-31"
      }
    ],
    "holder_distribution": {
      "institutional": 68.5,
      "individual": 20.3,
      "foreign": 11.2,
      "treasury": 0
    },
    "concentration_ratio": {
      "top1": 54.06,
      "top3": 68.48,
      "top5": 72.35,
      "top10": 78.92
    },
    "changes": {
      "last_period": "2025-09-30",
      "net_institutional_change": 2.5,
      "major_changes": [
        {
          "holder": "香港中央结算有限公司",
          "change_type": "增持",
          "change_shares": 50000000,
          "change_ratio": 0.4
        }
      ]
    }
  }
}
```

### 4.2 获取股东变动历史

#### 请求

```http
GET /api/v1/shareholders/{stock_code}/history
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `periods` | integer | 否 | `4` | 查询报告期数 |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "history": [
      {
        "report_date": "2025-12-31",
        "institutional_ratio": 68.5,
        "foreign_ratio": 11.2,
        "top10_concentration": 78.92,
        "net_institutional_change": 2.5
      },
      {
        "report_date": "2025-09-30",
        "institutional_ratio": 66.0,
        "foreign_ratio": 10.8,
        "top10_concentration": 77.45,
        "net_institutional_change": -1.2
      }
    ]
  }
}
```

---

## 5. 新闻 API

### 5.1 获取股票相关新闻

获取与指定股票相关的新闻资讯。

#### 请求

```http
GET /api/v1/news/{stock_code}
```

**Path Parameters:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `stock_code` | string | 是 | 股票代码 |

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `days` | integer | 否 | `7` | 过去几天 (1-30) |
| `limit` | integer | 否 | `20` | 返回数量 (1-50) |
| `source` | string | 否 | - | 新闻来源筛选 |
| `market` | string | 否 | `auto` | 市场类型 |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "name": "贵州茅台",
    "news": [
      {
        "id": "news_001",
        "headline": "贵州茅台发布2025年年报：净利润625亿元，同比增长18.5%",
        "summary": "贵州茅台今日发布2025年年度报告，实现营业收入1275亿元，同比增长15.2%；归属于上市公司股东的净利润625亿元，同比增长18.5%...",
        "content": "详细内容...",
        "source": "证券时报",
        "author": "张三",
        "url": "https://example.com/news/001",
        "image_url": "https://example.com/images/001.jpg",
        "category": "财报",
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "related_stocks": ["600519", "000858"],
        "published_at": "2026-03-25T08:30:00Z",
        "created_at": "2026-03-25T08:35:00Z"
      },
      {
        "id": "news_002",
        "headline": "茅台股价再创新高，市值突破2.2万亿",
        "summary": "受年报利好消息刺激，贵州茅台股价今日大涨3.5%，收盘价突破1800元...",
        "source": "新浪财经",
        "author": "李四",
        "url": "https://example.com/news/002",
        "category": "行情",
        "sentiment": "positive",
        "sentiment_score": 0.72,
        "published_at": "2026-03-25T15:00:00Z"
      }
    ],
    "meta": {
      "total": 35,
      "page": 1,
      "limit": 20,
      "date_range": {
        "from": "2026-03-18",
        "to": "2026-03-25"
      },
      "sources": ["证券时报", "新浪财经", "东方财富", "同花顺"],
      "sentiment_summary": {
        "positive": 18,
        "neutral": 12,
        "negative": 5
      }
    }
  }
}
```

### 5.2 获取市场热点新闻

#### 请求

```http
GET /api/v1/news/trending
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `market` | string | 否 | `A` | 市场类型 |
| `limit` | integer | 否 | `20` | 返回数量 |

#### 响应

```json
{
  "success": true,
  "data": {
    "news": [
      {
        "id": "trend_001",
        "headline": "央行宣布降准0.5个百分点",
        "summary": "中国人民银行决定于2026年4月1日下调金融机构存款准备金率0.5个百分点...",
        "source": "新华社",
        "url": "https://...",
        "category": "宏观",
        "impact_stocks": ["银行", "地产"],
        "published_at": "2026-03-25T18:00:00Z"
      }
    ],
    "hot_topics": [
      {"topic": "降准", "count": 125},
      {"topic": "AI芯片", "count": 89},
      {"topic": "新能源汽车", "count": 76}
    ]
  }
}
```

---

## 6. 投资组合管理 API

### 6.1 创建投资组合

#### 请求

```http
POST /api/v1/portfolio
```

**Request Body:**

```json
{
  "name": "我的价值投资组合",
  "description": "长期持有的优质股票",
  "currency": "CNY",
  "holdings": [
    {
      "stock_code": "600519",
      "market": "A",
      "shares": 100,
      "cost_price": 1650.00,
      "purchase_date": "2024-01-15"
    },
    {
      "stock_code": "000858",
      "market": "A",
      "shares": 200,
      "cost_price": 145.00,
      "purchase_date": "2024-02-20"
    }
  ]
}
```

#### 响应

```json
{
  "success": true,
  "data": {
    "portfolio_id": "pf_abc123",
    "name": "我的价值投资组合",
    "created_at": "2026-03-25T10:00:00Z",
    "holdings_count": 2,
    "total_value": 192900.00,
    "total_cost": 194000.00
  }
}
```

### 6.2 获取投资组合分析

#### 请求

```http
GET /api/v1/portfolio/{portfolio_id}/analysis
```

#### 响应

```json
{
  "success": true,
  "data": {
    "portfolio_id": "pf_abc123",
    "name": "我的价值投资组合",
    "currency": "CNY",
    "summary": {
      "total_value": 215000.00,
      "total_cost": 194000.00,
      "total_gain": 21000.00,
      "total_gain_percent": 10.82,
      "daily_gain": 3500.00,
      "daily_gain_percent": 1.65
    },
    "holdings": [
      {
        "stock_code": "600519",
        "name": "贵州茅台",
        "shares": 100,
        "cost_price": 1650.00,
        "current_price": 1850.00,
        "market_value": 185000.00,
        "gain": 20000.00,
        "gain_percent": 12.12,
        "weight": 86.05,
        "pe": 32.5,
        "roe": 28.56
      },
      {
        "stock_code": "000858",
        "name": "五粮液",
        "shares": 200,
        "cost_price": 145.00,
        "current_price": 150.00,
        "market_value": 30000.00,
        "gain": 1000.00,
        "gain_percent": 3.45,
        "weight": 13.95,
        "pe": 22.8,
        "roe": 25.12
      }
    ],
    "risk_analysis": {
      "concentration_risk": {
        "level": "high",
        "max_single_weight": 86.05,
        "recommendation": "建议分散持仓，单一股票权重不宜超过30%"
      },
      "sector_exposure": {
        "白酒": 100.0,
        "warning": "持仓过度集中在单一行业"
      },
      "valuation_risk": {
        "weighted_pe": 31.2,
        "market_avg_pe": 18.5,
        "assessment": "估值偏高"
      }
    },
    "performance": {
      "ytd_return": 12.5,
      "one_year_return": 18.2,
      "benchmark_return": 8.5,
      "alpha": 9.7,
      "beta": 0.85,
      "sharpe_ratio": 1.25
    },
    "recommendations": [
      {
        "type": "rebalance",
        "priority": "high",
        "message": "贵州茅台持仓占比过高(86%)，建议减持至30%以下",
        "action": "减持 600519"
      },
      {
        "type": "diversify",
        "priority": "medium",
        "message": "持仓全部为白酒行业，建议配置其他行业降低风险",
        "suggestions": ["银行业", "保险业", "消费电子"]
      }
    ]
  }
}
```

### 6.3 添加持仓

#### 请求

```http
POST /api/v1/portfolio/{portfolio_id}/holdings
```

**Request Body:**

```json
{
  "stock_code": "601318",
  "market": "A",
  "shares": 300,
  "cost_price": 45.50,
  "purchase_date": "2026-03-25"
}
```

### 6.4 更新持仓

#### 请求

```http
PATCH /api/v1/portfolio/{portfolio_id}/holdings/{stock_code}
```

**Request Body:**

```json
{
  "shares": 150,
  "cost_price": 1700.00
}
```

### 6.5 删除持仓

#### 请求

```http
DELETE /api/v1/portfolio/{portfolio_id}/holdings/{stock_code}
```

### 6.6 获取风险提示

#### 请求

```http
GET /api/v1/portfolio/{portfolio_id}/alerts
```

#### 响应

```json
{
  "success": true,
  "data": {
    "portfolio_id": "pf_abc123",
    "alerts": [
      {
        "id": "alert_001",
        "type": "concentration",
        "severity": "high",
        "title": "持仓集中度过高",
        "message": "贵州茅台占比86.05%，超过建议的30%上限",
        "stock_code": "600519",
        "created_at": "2026-03-25T10:00:00Z",
        "read": false
      },
      {
        "id": "alert_002",
        "type": "valuation",
        "severity": "medium",
        "title": "估值偏高预警",
        "message": "组合加权PE(31.2)显著高于市场平均(18.5)",
        "created_at": "2026-03-25T10:00:00Z",
        "read": true
      },
      {
        "id": "alert_003",
        "type": "price",
        "severity": "low",
        "title": "股价突破新高",
        "message": "贵州茅台今日收盘价1850元，创历史新高",
        "stock_code": "600519",
        "created_at": "2026-03-25T15:00:00Z",
        "read": false
      }
    ],
    "unread_count": 2
  }
}
```

---

## 7. 行情数据 API

### 7.1 获取实时行情

#### 请求

```http
GET /api/v1/quotes/{stock_code}
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `market` | string | 否 | `auto` | 市场类型 |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "name": "贵州茅台",
    "market": "A",
    "currency": "CNY",
    "price": 1850.00,
    "open": 1820.00,
    "high": 1865.00,
    "low": 1815.00,
    "previous_close": 1795.00,
    "change": 55.00,
    "change_percent": 3.06,
    "volume": 3250000,
    "amount": 5987500000,
    "turnover_rate": 0.26,
    "timestamp": "2026-03-25T15:00:00Z",
    "market_status": "closed"
  }
}
```

### 7.2 获取历史 K 线

#### 请求

```http
GET /api/v1/quotes/{stock_code}/history
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `period` | string | 否 | `1m` | 周期: `1d`, `1w`, `1m`, `3m`, `6m`, `1y`, `ytd` |
| `interval` | string | 否 | `1d` | K线间隔: `1d`, `1w`, `1M` |
| `start_date` | string | 否 | - | 开始日期 (YYYY-MM-DD) |
| `end_date` | string | 否 | - | 结束日期 (YYYY-MM-DD) |

#### 响应

```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "period": "1m",
    "bars": [
      {
        "date": "2026-03-25",
        "open": 1820.00,
        "high": 1865.00,
        "low": 1815.00,
        "close": 1850.00,
        "volume": 3250000,
        "amount": 5987500000,
        "change": 55.00,
        "change_percent": 3.06
      }
    ],
    "meta": {
      "count": 22,
      "start_date": "2026-02-25",
      "end_date": "2026-03-25"
    }
  }
}
```

---

## 8. 搜索与筛选 API

### 8.1 搜索股票

#### 请求

```http
GET /api/v1/search
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `q` | string | 是 | 搜索关键词 (股票名称或代码) |
| `market` | string | 否 | 市场类型 |
| `limit` | integer | 否 | 返回数量 (默认 10) |

#### 响应

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "stock_code": "600519",
        "name": "贵州茅台",
        "market": "A",
        "industry": "白酒",
        "highlight": "<em>茅台</em>"
      },
      {
        "stock_code": "600809",
        "name": "山西汾酒",
        "market": "A",
        "industry": "白酒",
        "highlight": "山西汾酒"
      }
    ],
    "total": 2,
    "query": "茅台"
  }
}
```

---

## 9. 数据源说明

### 9.1 A股数据源 (Ashare)

| 数据类型 | 接口 | 缓存时间 | 限制 |
|---------|------|---------|------|
| 实时行情 | `get_price` | 1分钟 | - |
| 股票列表 | `get_stock_list` | 1天 | - |
| 财务数据 | AkShare | 1小时 | - |

### 9.2 美股/港股数据源 (Finnhub)

| 数据类型 | 接口 | 缓存时间 | 限制 |
|---------|------|---------|------|
| 实时报价 | `/quote` | 1分钟 | 60 calls/min |
| 公司信息 | `/stock/profile2` | 1天 | 60 calls/min |
| 基本面 | `/stock/metric` | 1小时 | 60 calls/min |
| 新闻 | `/company-news` | 1小时 | 60 calls/min |

### 9.3 缓存策略

```python
CACHE_TTL = {
    # 行情数据
    'quote_realtime': 60,        # 1分钟
    'quote_history': 3600,       # 1小时
    
    # 财务数据
    'financials': 86400,         # 1天
    'balance_sheet': 86400,
    'cash_flow': 86400,
    
    # 股东数据
    'shareholders': 86400,       # 1天
    
    # 新闻数据
    'news': 3600,                # 1小时
    
    # 推荐结果
    'recommendations': 3600,     # 1小时
}
```

---

## 10. 限流规则

### 10.1 API 限流

| 端点类型 | 限制 | 窗口 |
|---------|------|------|
| 公开接口 | 100 次 | 1分钟 |
| 行情接口 | 60 次 | 1分钟 |
| 推荐接口 | 20 次 | 1分钟 |
| 写入接口 | 30 次 | 1分钟 |

### 10.2 限流响应

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请稍后再试",
    "retry_after": 45
  }
}
```

---

## 11. SDK 使用示例

### 11.1 JavaScript/TypeScript

```typescript
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
});

// 获取推荐股票
async function getRecommendations(market: string = 'A') {
  const response = await client.get('/stocks/recommend', {
    params: { market, min_roe: 15, limit: 10 }
  });
  return response.data;
}

// 获取财报数据
async function getFinancials(stockCode: string) {
  const response = await client.get(`/financials/${stockCode}`, {
    params: { years: 5 }
  });
  return response.data;
}

// 获取股东信息
async function getShareholders(stockCode: string) {
  const response = await client.get(`/shareholders/${stockCode}`);
  return response.data;
}
```

### 11.2 Python

```python
import requests

BASE_URL = 'http://localhost:8000/api/v1'

def get_recommendations(market='A', min_roe=15, limit=10):
    """获取推荐股票"""
    response = requests.get(f'{BASE_URL}/stocks/recommend', params={
        'market': market,
        'min_roe': min_roe,
        'limit': limit
    })
    return response.json()

def get_financials(stock_code, years=5):
    """获取财报数据"""
    response = requests.get(f'{BASE_URL}/financials/{stock_code}', params={
        'years': years
    })
    return response.json()

def get_shareholders(stock_code):
    """获取股东信息"""
    response = requests.get(f'{BASE_URL}/shareholders/{stock_code}')
    return response.json()

def get_news(stock_code, days=7):
    """获取相关新闻"""
    response = requests.get(f'{BASE_URL}/news/{stock_code}', params={
        'days': days
    })
    return response.json()

# 使用示例
if __name__ == '__main__':
    # 获取A股推荐
    recs = get_recommendations(market='A', min_roe=20)
    print(f"推荐股票: {len(recs['data'])} 只")
    
    # 获取茅台财报
    financials = get_financials('600519')
    print(f"财报时间线: {len(financials['data']['timeline'])} 年")
```

---

## 12. 变更日志

### v1.0 (2026-03-25)
- 初始版本发布
- 实现价值推荐 API
- 实现财报分析 API (三大报表)
- 实现持股查询 API
- 实现新闻 API
- 实现投资组合管理 API
- 支持 A股 (Ashare) + 美股/港股 (Finnhub) 数据源

---

## 附录：完整端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/stocks/recommend` | 价值投资推荐 |
| POST | `/stocks/sync` | 同步股票列表 |
| GET | `/financials/{code}` | 财报时间线 |
| GET | `/financials/{code}/balance-sheet` | 资产负债表 |
| GET | `/financials/{code}/income-statement` | 利润表 |
| GET | `/financials/{code}/cash-flow` | 现金流量表 |
| GET | `/shareholders/{code}` | 股东信息 |
| GET | `/shareholders/{code}/history` | 股东变动历史 |
| GET | `/news/{code}` | 股票相关新闻 |
| GET | `/news/trending` | 市场热点新闻 |
| POST | `/portfolio` | 创建投资组合 |
| GET | `/portfolio/{id}/analysis` | 组合分析 |
| POST | `/portfolio/{id}/holdings` | 添加持仓 |
| PATCH | `/portfolio/{id}/holdings/{code}` | 更新持仓 |
| DELETE | `/portfolio/{id}/holdings/{code}` | 删除持仓 |
| GET | `/portfolio/{id}/alerts` | 风险提示 |
| GET | `/quotes/{code}` | 实时行情 |
| GET | `/quotes/{code}/history` | 历史 K 线 |
| GET | `/search` | 搜索股票 |
| GET | `/health` | 健康检查 |

---

**文档维护**: 本规范将随项目演进持续更新。如有疑问或建议，请联系开发团队。
