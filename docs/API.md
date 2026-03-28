# ValueGraph API 文档

**版本**：v1.0  
**基础 URL**：http://localhost:8001  
**更新日期**：2026-03-22

## 接口列表

### 1. 健康检查
**GET** `/api/health`

**描述**：检查服务状态

**请求示例**：
```bash
curl http://localhost:8001/api/health
```

**响应示例**：
```json
{
  "status": "ok",
  "service": "valuegraph"
}
```

---

### 2. 获取推荐股票
**GET** `/api/stocks/recommend`

**描述**：获取价值投资推荐股票

**参数**：
- `market` (string): 市场类型（a-share 或 us-market）
- `top_n` (int): 返回数量，默认 10

**请求示例**：
```bash
curl "http://localhost:8001/api/stocks/recommend?market=a-share&top_n=10"
```

**响应示例**：
```json
{
  "success": true,
  "market": "a-share",
  "count": 10,
  "filters": {
    "min_roe": 15.0,
    "max_debt_ratio": 50.0
  },
  "data": [
    {
      "代码": "600519",
      "名称": "贵州茅台",
      "roe": 24.32,
      "debt_ratio": 12.81,
      "score": 55.76
    }
  ]
}
```

**筛选标准**：
- ROE ≥ 15%（盈利能力强）
- 负债率 ≤ 50%（财务健康）

**评分公式**：
```
Score = ROE × 0.5 + (100 - 负债率) × 0.5
```

---

### 3. 获取股票详情
**GET** `/api/stocks/{stock_code}`

**描述**：获取股票详情（财务数据 + 股东信息）

**参数**：
- `stock_code` (string): 股票代码（如 600519）

**请求示例**：
```bash
curl http://localhost:8001/api/stocks/600519
```

**响应示例**：
```json
{
  "stock_code": "600519",
  "financial_data": {
    "roe": 24.32,
    "roa": 21.21,
    "grossprofit_margin": 91.29,
    "debt_ratio": 12.81
  },
  "shareholders": [
    {
      "股东名称": "中国贵州茅台酒厂（集团）有限责任公司",
      "持股数量": "678381195",
      "持股比例": "54.06%"
    }
  ]
}
```

---

## Week 4 新增接口

### 1. 获取资产负债表
**GET** `/api/v1/financial/{stock_code}/balance_sheet`

**描述**：获取指定股票的资产负债表数据

**参数**：
- `stock_code` (string): 股票代码（如 000001.SZ）
- `years` (int, optional): 年数，默认 5

**请求示例**：
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/balance_sheet?years=5"
```

**响应示例**：
```json
{
  "success": true,
  "stock_code": "000001.SZ",
  "count": 5,
  "data": [
    {
      "end_date": "2023-12-31",
      "total_assets": 1000000000,
      "total_liabilities": 500000000,
      "total_equity": 500000000,
      "current_assets": 600000000,
      "current_liabilities": 300000000
    }
  ]
}
```

---

### 2. 获取利润表
**GET** `/api/v1/financial/{stock_code}/income_statement`

**描述**：获取指定股票的利润表数据

**参数**：
- `stock_code` (string): 股票代码（如 000001.SZ）
- `years` (int, optional): 年数，默认 5

**请求示例**：
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/income_statement?years=5"
```

**响应示例**：
```json
{
  "success": true,
  "stock_code": "000001.SZ",
  "count": 5,
  "data": [
    {
      "end_date": "2023-12-31",
      "revenue": 800000000,
      "net_profit": 150000000,
      "gross_profit": 400000000,
      "operating_profit": 200000000
    }
  ]
}
```

---

### 3. 获取现金流量表
**GET** `/api/v1/financial/{stock_code}/cash_flow_statement`

**描述**：获取指定股票的现金流量表数据

**参数**：
- `stock_code` (string): 股票代码（如 000001.SZ）
- `years` (int, optional): 年数，默认 5

**请求示例**：
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/cash_flow_statement?years=5"
```

**响应示例**：
```json
{
  "success": true,
  "stock_code": "000001.SZ",
  "count": 5,
  "data": [
    {
      "end_date": "2023-12-31",
      "operating_cash_flow": 180000000,
      "investing_cash_flow": -80000000,
      "financing_cash_flow": -60000000,
      "free_cash_flow": 100000000
    }
  ]
}
```

---

### 4. 财务指标计算
**GET** `/api/v1/financial/{stock_code}/metrics`

**描述**：计算并返回指定股票的综合财务指标

**参数**：
- `stock_code` (string): 股票代码（如 000001.SZ）

**请求示例**：
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/metrics"
```

**响应示例**：
```json
{
  "success": true,
  "stock_code": "000001.SZ",
  "metrics": {
    "roe": 15.5,
    "roa": 12.3,
    "gross_margin": 45.6,
    "debt_ratio": 30.2,
    "current_ratio": 1.8,
    "free_cash_flow": 50000000,
    "inventory_turnover": 8.5,
    "receivables_turnover": 12.3
  }
}
```

**指标说明**：
- **盈利能力**：ROE、ROA、毛利率
- **偿债能力**：资产负债率、流动比率
- **运营能力**：存货周转率、应收账款周转率
- **现金流**：自由现金流

---

### 5. 异常检测
**GET** `/api/v1/financial/{stock_code}/anomalies`

**描述**：检测财务数据中的异常情况

**参数**：
- `stock_code` (string): 股票代码（如 000001.SZ）

**请求示例**：
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/anomalies"
```

**响应示例**：
```json
{
  "success": true,
  "stock_code": "000001.SZ",
  "anomalies": [
    {
      "type": "zscore_anomaly",
      "field": "revenue",
      "period": "2023-Q3",
      "value": 500000000,
      "z_score": 3.5,
      "severity": "high",
      "description": "营收异常波动，Z-score 超过阈值"
    },
    {
      "type": "missing_data",
      "field": "cash_flow",
      "period": "2021-Q2",
      "severity": "medium",
      "description": "缺失现金流数据"
    }
  ],
  "total_count": 2
}
```

**异常类型**：
- **Z-score 异常**：统计异常值检测
- **缺失数据**：财报期连续性检测
- **负值异常**：不应为负的字段检测
- **剧烈变化**：环比/同比异常波动
- **数据质量**：勾稽关系验证

---

### 6. 数据同步
**POST** `/api/v1/financial/{stock_code}/sync`

**描述**：手动触发财务数据同步（从数据源拉取最新数据）

**参数**：
- `stock_code` (string): 股票代码（如 000001.SZ）

**请求示例**：
```bash
curl -X POST "http://localhost:8001/api/v1/financial/000001.SZ/sync"
```

**响应示例**：
```json
{
  "success": true,
  "stock_code": "000001.SZ",
  "sync_result": {
    "balance_sheet": {
      "updated": 5,
      "inserted": 0,
      "failed": 0
    },
    "income_statement": {
      "updated": 5,
      "inserted": 0,
      "failed": 0
    },
    "cash_flow_statement": {
      "updated": 5,
      "inserted": 0,
      "failed": 0
    }
  },
  "data_source": "tushare",
  "synced_at": "2026-03-22T23:30:00Z"
}
```

---

## Week 5 新增前端组件

### 1. FinancialChart - 时间线图表组件

**功能**：展示财务数据的时间序列变化

**特性**：
- 多指标显示（ROE、ROA、负债率等）
- 支持缩放和拖动
- 悬停 tooltip 显示详细数据
- 图例可点击切换显示/隐藏

**使用示例**：
```typescript
import { FinancialChart } from '@/components/FinancialChart'

<FinancialChart
  stockCode="600519"
  metrics={['roe', 'roa', 'debt_ratio']}
  years={5}
  loading={false}
/>
```

**Props**：
- `stockCode` (string): 股票代码
- `metrics` (string[]): 指标数组
- `years` (number): 显示年数，默认 5
- `loading` (boolean): 加载状态

**技术实现**：
- 基于 ECharts 6.0.0
- 使用 echarts-for-react 3.0.6
- 响应式设计，支持移动端

---

### 2. MultiMetricComparison - 多指标对比组件

**功能**：对比多个财务指标的历史变化

**特性**：
- 下拉框多选指标
- 实时更新图表
- 支持的指标：
  - ROE (净资产收益率)
  - ROA (总资产收益率)
  - 负债率
  - 收入
  - 净利润
  - 毛利率
  - 流动比率
  - 自由现金流

**使用示例**：
```typescript
import { MultiMetricComparison } from '@/components/MultiMetricComparison'

<MultiMetricComparison
  stockCode="000001.SZ"
  defaultMetrics={['roe', 'roa', 'gross_margin']}
  years={5}
/>
```

**Props**：
- `stockCode` (string): 股票代码
- `defaultMetrics` (string[]): 默认选中的指标
- `years` (number): 显示年数

**技术实现**：
- Ant Design Select 组件（多选模式）
- ECharts 折线图
- useState 管理选中指标

---

### 3. FinancialRadar - 财务雷达图组件

**功能**：综合展示财务健康度的五维指标

**维度**：
1. ROE (净资产收益率)
2. ROA (总资产收益率)
3. 毛利率
4. 流动比率
5. 自由现金流

**特性**：
- 数据归一化到 0-100 范围
- 悬停显示实际值
- 直观展示财务健康状况

**使用示例**：
```typescript
import { FinancialRadar } from '@/components/FinancialRadar'

const radarData = {
  roe: 24.5,
  roa: 18.3,
  grossMargin: 45.2,
  currentRatio: 2.1,
  freeCashFlow: 1500000000
}

<FinancialRadar
  metrics={radarData}
  loading={false}
/>
```

**Props**：
- `metrics` (object): 财务指标数据
- `loading` (boolean): 加载状态

**技术实现**：
- ECharts radar 图表类型
- 自定义 tooltip 格式化
- 数值归一化算法

---

### 4. DuPontTree - 杜邦分析树组件

**功能**：展示杜邦分析的三层分解结构

**公式**：ROE = 净利润率 × 资产周转率 × 权益乘数

**特性**：
- 树形结构展示
- 可展开/收起
- 包含公式说明
- 显示各指标数值

**使用示例**：
```typescript
import { DuPontTree } from '@/components/DuPontTree'

const duPontData = {
  roe: 24.5,
  children: [
    { label: '净利润率', value: 15.2 },
    { label: '资产周转率', value: 0.8 },
    { label: '权益乘数', value: 2.0 }
  ]
}

<DuPontTree
  data={duPontData}
  loading={false}
/>
```

**Props**：
- `data` (object): 杜邦分析数据
- `loading` (boolean): 加载状态

**技术实现**：
- Ant Design Tree 组件
- 递归渲染树结构
- 自定义节点样式

---

### 技术栈

**依赖库**：
- `echarts@6.0.0` - 图表库
- `echarts-for-react@3.0.6` - React 封装
- `antd@6.3.3` - UI 组件库

**性能优化**：
- 使用 `useMemo` 缓存计算结果
- 按需加载 ECharts 组件
- 数据懒加载

**错误处理**：
- API 失败时降级到模拟数据
- 友好的错误提示
- Console 日志记录

---

**文档维护**：Documenter  
**最后更新**：2026-03-22 23:50
