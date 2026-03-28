# 财务数据说明文档

**版本**：v0.2.0  
**更新日期**：2026-03-22

## 财务报表

### 1. 资产负债表（Balance Sheet）
反映公司在特定日期的财务状况。

**主要字段**：
- `total_assets`: 总资产
- `total_liabilities`: 总负债
- `total_equity`: 净资产
- `current_assets`: 流动资产
- `current_liabilities`: 流动负债
- `non_current_assets`: 非流动资产
- `non_current_liabilities`: 非流动负债
- `cash_and_equivalents`: 货币资金
- `inventory`: 存货
- `accounts_receivable`: 应收账款

**数据来源**：
- Tushare Pro: `pro.balancesheet()`
- AkShare: `stock_balance_sheet_by_report_em()`

---

### 2. 利润表（Income Statement）
反映公司在一定期间的经营成果。

**主要字段**：
- `revenue`: 营业收入
- `net_profit`: 净利润
- `gross_profit`: 毛利润
- `operating_profit`: 营业利润
- `operating_cost`: 营业成本
- `selling_expense`: 销售费用
- `admin_expense`: 管理费用
- `financial_expense`: 财务费用
- `ebit`: 息税前利润
- `ebitda`: 息税折旧摊销前利润

**数据来源**：
- Tushare Pro: `pro.income()`
- AkShare: `stock_profit_sheet_by_report_em()`

---

### 3. 现金流量表（Cash Flow Statement）
反映公司现金流入和流出情况。

**主要字段**：
- `operating_cash_flow`: 经营活动现金流
- `investing_cash_flow`: 投资活动现金流
- `financing_cash_flow`: 筹资活动现金流
- `free_cash_flow`: 自由现金流
- `cash_received_from_sales`: 销售商品收到的现金
- `cash_paid_for_goods`: 购买商品支付的现金
- `cash_paid_to_employees`: 支付给职工的现金

**数据来源**：
- Tushare Pro: `pro.cashflow()`
- AkShare: `stock_cash_flow_sheet_by_report_em()`

---

## 财务指标

### 盈利能力
- **ROE**（净资产收益率）= 净利润 / 净资产 × 100%
  - 衡量股东权益回报，越高越好
  - 价值投资标准：≥ 15%
  
- **ROA**（总资产净利率）= 净利润 / 总资产 × 100%
  - 衡量资产利用效率
  - 一般标准：≥ 10%
  
- **毛利率** = 毛利润 / 营业收入 × 100%
  - 衡量产品竞争力
  - 不同行业标准差异大

- **净利率** = 净利润 / 营业收入 × 100%
  - 衡量整体盈利能力

### 偿债能力
- **资产负债率** = 总负债 / 总资产 × 100%
  - 衡量财务风险
  - 价值投资标准：≤ 50%
  
- **流动比率** = 流动资产 / 流动负债
  - 衡量短期偿债能力
  - 一般标准：≥ 1.5
  
- **速动比率** = (流动资产 - 存货) / 流动负债
  - 更严格的短期偿债能力指标
  - 一般标准：≥ 1.0

### 运营能力
- **存货周转率** = 营业成本 / 平均存货
  - 衡量存货管理效率
  - 越高越好
  
- **应收账款周转率** = 营业收入 / 平均应收账款
  - 衡量应收账款回收效率
  - 越高越好
  
- **总资产周转率** = 营业收入 / 平均总资产
  - 衡量资产运营效率

### 现金流
- **自由现金流** = 经营现金流 + 投资现金流
  - 衡量企业可自由支配的现金
  - 正值表示企业造血能力强
  
- **现金流质量** = 经营现金流 / 净利润
  - 衡量利润的现金含量
  - 一般标准：≥ 1.0

---

## 数据来源

### Tushare Pro
- **优势**：
  - 数据质量高，字段完整
  - 历史数据丰富（可追溯到 2000 年）
  - 数据更新及时
  
- **限制**：
  - 需要积分权限（部分接口需要 5000+ 积分）
  - 有调用频率限制（每分钟 200-800 次）
  - 需要注册获取 token
  
- **接口**：
  - `pro.balancesheet()`: 资产负债表
  - `pro.income()`: 利润表
  - `pro.cashflow()`: 现金流量表
  - `pro.daily()`: 日线行情
  
- **文档**：https://tushare.pro/document/2

### AkShare
- **优势**：
  - 完全免费开源，无需注册
  - 即时可用，无权限限制
  - 支持多数据源（东方财富、新浪等）
  
- **限制**：
  - 字段可能不完整
  - 历史数据年限较短
  - 部分接口不稳定
  
- **接口**：
  - `stock_balance_sheet_by_report_em()`: 资产负债表
  - `stock_profit_sheet_by_report_em()`: 利润表
  - `stock_cash_flow_sheet_by_report_em()`: 现金流量表
  
- **文档**：https://akshare.akfamily.xyz

### 双数据源策略
1. **优先使用 Tushare Pro**（数据质量高）
2. **失败时降级到 AkShare**（兜底方案）
3. **自动重试机制**（网络异常时重试 3 次）
4. **数据源标识**（记录数据来源）

---

## 异常检测

### 1. Z-score 异常值检测
识别财务数据中的异常波动。

**公式**：`Z = (X - μ) / σ`

**阈值**：|Z| > 3 为异常

**检测字段**：
- 营业收入
- 净利润
- 总资产
- 经营现金流

**应用场景**：
- 发现财务造假线索
- 识别经营异常波动
- 数据质量预警

### 2. 缺失数据检测
检测财报期是否连续。

**检测逻辑**：
- 检查季度数据是否连续（Q1, Q2, Q3, Q4）
- 检查年度数据是否连续（2021, 2022, 2023）
- 识别缺失的报告期

**严重程度**：
- **高**：连续 2 个季度以上缺失
- **中**：单个季度缺失
- **低**：非核心字段缺失

### 3. 负值检测
检测不应为负的字段。

**检测字段**：
- 营业收入（应为正）
- 总资产（应为正）
- 净资产（应为正，除非资不抵债）
- 存货（应为正）

**特殊情况**：
- 净利润可为负（亏损）
- 经营现金流可为负（经营困难）
- 自由现金流可为负（大额投资）

### 4. 剧烈变化检测
检测环比/同比变化超过阈值的数据。

**阈值设定**：
- **环比变化**：> 50% 为异常
- **同比变化**：> 100% 为异常
- **特殊情况**：从负值到正值不适用

**检测字段**：
- 营业收入
- 净利润
- 总资产
- 经营现金流

### 5. 数据质量验证
验证财务报表之间的勾稽关系。

**勾稽关系**：
- 资产负债表：总资产 = 总负债 + 净资产
- 利润表：营业利润 = 营业收入 - 营业成本 - 费用
- 现金流表：自由现金流 = 经营现金流 + 投资现金流

**允许误差**：± 1%（四舍五入误差）

---

## 数据存储

### PostgreSQL 表结构

#### balance_sheets（资产负债表）
```sql
CREATE TABLE balance_sheets (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    end_date DATE NOT NULL,
    total_assets DECIMAL(20, 2),
    total_liabilities DECIMAL(20, 2),
    total_equity DECIMAL(20, 2),
    current_assets DECIMAL(20, 2),
    current_liabilities DECIMAL(20, 2),
    data_source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, end_date)
);
```

#### income_statements（利润表）
```sql
CREATE TABLE income_statements (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    end_date DATE NOT NULL,
    revenue DECIMAL(20, 2),
    net_profit DECIMAL(20, 2),
    gross_profit DECIMAL(20, 2),
    operating_profit DECIMAL(20, 2),
    data_source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, end_date)
);
```

#### cash_flow_statements（现金流量表）
```sql
CREATE TABLE cash_flow_statements (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    end_date DATE NOT NULL,
    operating_cash_flow DECIMAL(20, 2),
    investing_cash_flow DECIMAL(20, 2),
    financing_cash_flow DECIMAL(20, 2),
    free_cash_flow DECIMAL(20, 2),
    data_source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, end_date)
);
```

### 索引优化
- `idx_balance_ts_code`: 股票代码索引
- `idx_balance_end_date`: 报告期索引
- `idx_income_ts_code`: 利润表股票代码索引
- `idx_cashflow_ts_code`: 现金流表股票代码索引

**性能优化**：
- 联合索引：(ts_code, end_date)
- 分区表：按年份分区
- 定期 VACUUM 和 ANALYZE

### 数据更新
- **频率**：季度（跟随财报发布）
- **方式**：增量更新 + 去重
- **策略**：UPSERT（存在则更新，不存在则插入）

**更新流程**：
1. 从数据源拉取最新数据
2. 检查是否存在（ts_code + end_date）
3. 存在：更新记录
4. 不存在：插入新记录
5. 记录数据来源和更新时间

---

## 使用示例

### Python

#### 获取财务报表
```python
from app.services import FinancialStatementService

# 初始化服务
service = FinancialStatementService(token="your_tushare_token")

# 获取资产负债表
balance = await service.get_balance_sheet('000001.SZ', years=5)
print(f"获取到 {len(balance)} 年资产负债表数据")

# 获取利润表
income = await service.get_income_statement('000001.SZ', years=5)
print(f"获取到 {len(income)} 年利润表数据")

# 获取现金流量表
cashflow = await service.get_cash_flow_statement('000001.SZ', years=5)
print(f"获取到 {len(cashflow)} 年现金流量表数据")
```

#### 计算财务指标
```python
from app.services import FinancialCalculator

# 假设已有财务数据
balance_data = balance[0]
income_data = income[0]
cashflow_data = cashflow[0]

# 计算所有指标
metrics = FinancialCalculator.calculate_all_metrics(
    balance_data, 
    income_data, 
    cashflow_data
)

print(f"ROE: {metrics['roe']:.2f}%")
print(f"ROA: {metrics['roa']:.2f}%")
print(f"毛利率: {metrics['gross_margin']:.2f}%")
print(f"资产负债率: {metrics['debt_ratio']:.2f}%")
print(f"流动比率: {metrics['current_ratio']:.2f}")
print(f"自由现金流: {metrics['free_cash_flow']:,.0f}")
```

#### 检测异常
```python
from app.services import AnomalyDetector

# 检测所有异常
anomalies = AnomalyDetector.detect_all_anomalies(
    balance_list=balance,
    income_list=income,
    cashflow_list=cashflow
)

# 输出检测结果
for anomaly in anomalies:
    print(f"[{anomaly['severity'].upper()}] {anomaly['type']}: {anomaly['description']}")
    print(f"  字段: {anomaly['field']}, 期间: {anomaly['period']}")
```

#### 数据同步
```python
from app.services import DataSyncService

# 初始化同步服务
sync_service = DataSyncService()

# 同步单只股票
result = await sync_service.sync_stock('000001.SZ')
print(f"同步完成: {result['success']}")
print(f"数据来源: {result['data_source']}")
print(f"资产负债表: 更新 {result['balance_sheet']['updated']} 条")
print(f"利润表: 更新 {result['income_statement']['updated']} 条")
print(f"现金流量表: 更新 {result['cash_flow_statement']['updated']} 条")
```

### REST API

#### 获取资产负债表
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/balance_sheet?years=5"
```

#### 获取财务指标
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/metrics"
```

#### 检测异常
```bash
curl "http://localhost:8001/api/v1/financial/000001.SZ/anomalies"
```

#### 触发数据同步
```bash
curl -X POST "http://localhost:8001/api/v1/financial/000001.SZ/sync"
```

---

## 最佳实践

### 1. 数据缓存
- 使用 Redis 缓存热门股票数据
- 缓存时间：1 小时（财报季）或 24 小时（平时）
- 缓存键：`financial:{stock_code}:{report_type}:{years}`

### 2. 错误处理
- 网络超时：重试 3 次，间隔 1-2-5 秒
- 数据源失败：自动降级到备用数据源
- 数据异常：记录日志，返回友好错误信息

### 3. 性能优化
- 批量查询：一次查询多只股票
- 异步处理：使用 Celery 异步同步数据
- 分页查询：大数据量时使用分页

### 4. 数据验证
- 输入验证：验证股票代码格式
- 输出验证：验证数据完整性和合理性
- 异常监控：实时监控异常检测结果

---

## 更新日志

### v0.2.0 (2026-03-22)
- ✅ 新增三大财务报表接口
- ✅ 新增财务指标计算接口
- ✅ 新增异常检测接口
- ✅ 新增数据同步接口
- ✅ 支持 Tushare + AkShare 双数据源
- ✅ 实现 5 种异常检测算法
- ✅ 完成 21 个单元测试

### v0.1.0 (2026-03-15)
- ✅ 初始化项目结构
- ✅ 实现基础 API 框架

---

**文档维护**：Documenter  
**最后更新**：2026-03-22 23:35
