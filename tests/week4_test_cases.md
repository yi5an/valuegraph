# Week 4 财报数据功能测试用例

**项目**: ValueAnalyzer - 股票价值分析系统  
**测试阶段**: Week 4（财报数据完善）  
**测试范围**: 财务数据获取、存储、计算、异常检测  
**创建日期**: 2026-03-22  
**测试工程师**: @tester

---

## 📋 测试概览

### 测试目标
1. 验证财务数据获取的准确性和稳定性
2. 验证数据存储的完整性和一致性
3. 验证财务指标计算的准确性
4. 验证异常检测功能的有效性
5. 验证系统性能指标

### 测试环境
- **数据源**: Tushare Pro API, AkShare
- **数据库**: PostgreSQL / MySQL
- **测试股票**: 贵州茅台 (600519)
- **测试数据范围**: 2015-2024（10年历史数据）

### 测试数据文件
- `week4_test_data.json` - 测试数据集
- `week4_validation_data.json` - 验证数据集

---

## 1️⃣ 财务数据获取测试

### 1.1 获取资产负债表（正常）

**测试ID**: TC-FETCH-001  
**优先级**: P0  
**前置条件**: 
- Tushare API token 有效
- 网络连接正常

**测试步骤**:
1. 调用 `get_balance_sheet(stock_code='600519', start_date='2020-01-01', end_date='2024-12-31')`
2. 验证返回数据格式
3. 验证数据完整性

**预期结果**:
- ✅ 返回 HTTP 200
- ✅ 数据格式为 JSON
- ✅ 包含以下字段: `total_assets`, `total_liabilities`, `owners_equity`, `current_assets`, `current_liabilities`
- ✅ 数据条数 >= 20（年度+季度报告）
- ✅ 日期按降序排列

**验证方法**:
```python
assert response.status_code == 200
assert 'total_assets' in data[0]
assert len(data) >= 20
```

---

### 1.2 获取利润表（正常）

**测试ID**: TC-FETCH-002  
**优先级**: P0  
**前置条件**: 
- Tushare API token 有效
- 网络连接正常

**测试步骤**:
1. 调用 `get_income_statement(stock_code='600519', start_date='2020-01-01', end_date='2024-12-31')`
2. 验证返回数据格式
3. 验证数据完整性

**预期结果**:
- ✅ 返回 HTTP 200
- ✅ 数据格式为 JSON
- ✅ 包含以下字段: `total_revenue`, `operating_costs`, `gross_profit`, `net_profit`
- ✅ 营业收入 > 0
- ✅ 毛利润 = 营业收入 - 营业成本

**验证方法**:
```python
assert data[0]['total_revenue'] > 0
assert data[0]['gross_profit'] == data[0]['total_revenue'] - data[0]['operating_costs']
```

---

### 1.3 获取现金流量表（正常）

**测试ID**: TC-FETCH-003  
**优先级**: P0  
**前置条件**: 
- Tushare API token 有效
- 网络连接正常

**测试步骤**:
1. 调用 `get_cash_flow_statement(stock_code='600519', start_date='2020-01-01', end_date='2024-12-31')`
2. 验证返回数据格式
3. 验证现金流平衡关系

**预期结果**:
- ✅ 返回 HTTP 200
- ✅ 数据格式为 JSON
- ✅ 包含以下字段: `net_cash_flow_from_operating`, `net_cash_flow_from_investing`, `net_cash_flow_from_financing`
- ✅ 现金增加 = 经营现金流 + 投资现金流 + 筹资现金流

**验证方法**:
```python
calculated_increase = (data[0]['net_cash_flow_from_operating'] + 
                       data[0]['net_cash_flow_from_investing'] + 
                       data[0]['net_cash_flow_from_financing'])
assert abs(calculated_increase - data[0]['cash_increase']) < 1000  # 允许1元误差
```

---

### 1.4 数据源降级测试（Tushare → AkShare）

**测试ID**: TC-FETCH-004  
**优先级**: P1  
**前置条件**: 
- Tushare API 暂时不可用（模拟）
- AkShare 已配置

**测试步骤**:
1. 模拟 Tushare API 返回 429 或 500 错误
2. 调用 `get_balance_sheet(stock_code='600519')`
3. 验证系统自动降级到 AkShare

**预期结果**:
- ✅ 系统记录 Tushare 失败日志
- ✅ 自动切换到 AkShare 数据源
- ✅ 返回数据格式一致
- ✅ 数据准确性验证通过
- ✅ 降级时间 < 3s

**验证方法**:
```python
# 检查日志中是否有降级记录
assert 'fallback to akshare' in logs
assert data['data_source'] == 'akshare'
```

---

### 1.5 网络异常处理

**测试ID**: TC-FETCH-005  
**优先级**: P1  
**前置条件**: 
- 模拟网络异常

**测试步骤**:
1. 断开网络连接
2. 调用 `get_balance_sheet(stock_code='600519')`
3. 验证错误处理

**预期结果**:
- ✅ 返回明确的错误信息
- ✅ 错误码为 `NETWORK_ERROR`
- ✅ 包含重试建议
- ✅ 记录错误日志

**验证方法**:
```python
assert response.status_code == 503
assert response.json()['error_code'] == 'NETWORK_ERROR'
assert 'retry' in response.json()['message'].lower()
```

---

## 2️⃣ 数据存储测试

### 2.1 存储资产负债表（正常）

**测试ID**: TC-STORE-001  
**优先级**: P0  
**前置条件**: 
- 数据库连接正常
- 数据格式正确

**测试步骤**:
1. 准备资产负债表数据（JSON 格式）
2. 调用 `save_balance_sheet(data)`
3. 查询数据库验证存储结果

**预期结果**:
- ✅ 返回成功状态
- ✅ 数据库中新增记录
- ✅ 所有字段正确存储
- ✅ 数据类型正确（数值字段为 DECIMAL）

**验证方法**:
```python
# 查询数据库
saved_data = db.query("SELECT * FROM balance_sheets WHERE stock_code='600519' AND report_date='2024-12-31'")
assert saved_data is not None
assert saved_data['total_assets'] == 275000000000
```

---

### 2.2 存储利润表（正常）

**测试ID**: TC-STORE-002  
**优先级**: P0  
**前置条件**: 
- 数据库连接正常
- 数据格式正确

**测试步骤**:
1. 准备利润表数据
2. 调用 `save_income_statement(data)`
3. 验证存储结果

**预期结果**:
- ✅ 数据成功存储
- ✅ 字段完整
- ✅ 外键关联正确

**验证方法**:
```sql
SELECT COUNT(*) FROM income_statements 
WHERE stock_code='600519' AND report_date='2024-12-31';
-- 期望结果: 1
```

---

### 2.3 存储现金流量表（正常）

**测试ID**: TC-STORE-003  
**优先级**: P0  
**前置条件**: 
- 数据库连接正常
- 数据格式正确

**测试步骤**:
1. 准备现金流量表数据
2. 调用 `save_cash_flow_statement(data)`
3. 验证存储结果

**预期结果**:
- ✅ 数据成功存储
- ✅ 现金流平衡关系正确
- ✅ 与资产负债表现金字段一致

**验证方法**:
```python
# 验证现金字段一致性
cash_flow = get_cash_flow_statement('600519', '2024-12-31')
balance = get_balance_sheet('600519', '2024-12-31')
assert cash_flow['cash_at_end'] == balance['cash_and_equivalents']
```

---

### 2.4 重复数据检测

**测试ID**: TC-STORE-004  
**优先级**: P1  
**前置条件**: 
- 数据库中已存在相同数据

**测试步骤**:
1. 尝试插入重复的资产负债表数据（相同股票代码和报告日期）
2. 验证系统处理

**预期结果**:
- ✅ 系统检测到重复数据
- ✅ 拒绝插入或更新现有记录
- ✅ 返回提示信息
- ✅ 不产生重复记录

**验证方法**:
```python
# 第一次插入
result1 = save_balance_sheet(data)
assert result1['status'] == 'created'

# 第二次插入（重复）
result2 = save_balance_sheet(data)
assert result2['status'] == 'duplicate' or result2['status'] == 'updated'

# 验证唯一记录
count = db.query("SELECT COUNT(*) FROM balance_sheets WHERE stock_code='600519' AND report_date='2024-12-31'")
assert count == 1
```

---

### 2.5 批量存储性能

**测试ID**: TC-STORE-005  
**优先级**: P2  
**前置条件**: 
- 准备 1000 条财务数据
- 数据库连接正常

**测试步骤**:
1. 准备 1000 条资产负债表数据
2. 调用 `batch_save_balance_sheets(data_list)`
3. 记录执行时间

**预期结果**:
- ✅ 批量插入成功
- ✅ 执行时间 < 10s
- ✅ 无数据丢失
- ✅ 使用事务保证原子性

**验证方法**:
```python
import time
start_time = time.time()
result = batch_save_balance_sheets(data_1000)
end_time = time.time()

assert result['success_count'] == 1000
assert (end_time - start_time) < 10
```

---

## 3️⃣ 财务指标计算测试

### 3.1 ROE 计算准确性

**测试ID**: TC-CALC-001  
**优先级**: P0  
**计算公式**: `ROE = 净利润 / 平均所有者权益 * 100%`

**测试步骤**:
1. 使用贵州茅台 2024 年数据
2. 调用 `calculate_roe(stock_code='600519', year=2024)`
3. 与东方财富数据对比

**测试数据**:
- 净利润（归母）: 805 亿
- 期初所有者权益: 1870 亿
- 期末所有者权益: 2000 亿
- 预期 ROE: 41.67%

**预期结果**:
- ✅ 计算结果 = 41.67% (误差 < 0.1%)
- ✅ 与东方财富数据一致（误差 < 1%）

**验证方法**:
```python
roe = calculate_roe('600519', 2024)
expected_roe = 805 / ((1870 + 2000) / 2) * 100
assert abs(roe - expected_roe) < 0.1
assert abs(roe - 41.67) < 1.0
```

---

### 3.2 ROA 计算准确性

**测试ID**: TC-CALC-002  
**优先级**: P0  
**计算公式**: `ROA = 净利润 / 平均总资产 * 100%`

**测试步骤**:
1. 使用贵州茅台 2024 年数据
2. 调用 `calculate_roa(stock_code='600519', year=2024)`
3. 验证计算结果

**测试数据**:
- 净利润: 810 亿
- 期初总资产: 2550 亿
- 期末总资产: 2750 亿
- 预期 ROA: 30.56%

**预期结果**:
- ✅ 计算结果 = 30.56% (误差 < 0.1%)

**验证方法**:
```python
roa = calculate_roa('600519', 2024)
expected_roa = 810 / ((2550 + 2750) / 2) * 100
assert abs(roa - expected_roa) < 0.1
```

---

### 3.3 资产负债率计算准确性

**测试ID**: TC-CALC-003  
**优先级**: P0  
**计算公式**: `资产负债率 = 总负债 / 总资产 * 100%`

**测试步骤**:
1. 使用贵州茅台 2024 年数据
2. 调用 `calculate_debt_ratio(stock_code='600519', year=2024)`

**测试数据**:
- 总负债: 750 亿
- 总资产: 2750 亿
- 预期资产负债率: 27.27%

**预期结果**:
- ✅ 计算结果 = 27.27% (误差 < 0.01%)

**验证方法**:
```python
debt_ratio = calculate_debt_ratio('600519', 2024)
expected = 750 / 2750 * 100
assert abs(debt_ratio - expected) < 0.01
```

---

### 3.4 毛利率计算准确性

**测试ID**: TC-CALC-004  
**优先级**: P0  
**计算公式**: `毛利率 = (营业收入 - 营业成本) / 营业收入 * 100%`

**测试步骤**:
1. 使用贵州茅台 2024 年数据
2. 调用 `calculate_gross_margin(stock_code='600519', year=2024)`

**测试数据**:
- 营业收入: 1495 亿
- 营业成本: 120 亿
- 预期毛利率: 91.97%

**预期结果**:
- ✅ 计算结果 = 91.97% (误差 < 0.01%)
- ✅ 茅台毛利率应 > 90%

**验证方法**:
```python
gross_margin = calculate_gross_margin('600519', 2024)
expected = (1495 - 120) / 1495 * 100
assert abs(gross_margin - expected) < 0.01
assert gross_margin > 90
```

---

### 3.5 流动比率计算准确性

**测试ID**: TC-CALC-005  
**优先级**: P0  
**计算公式**: `流动比率 = 流动资产 / 流动负债`

**测试步骤**:
1. 使用贵州茅台 2024 年数据
2. 调用 `calculate_current_ratio(stock_code='600519', year=2024)`

**测试数据**:
- 流动资产: 2200 亿
- 流动负债: 700 亿
- 预期流动比率: 3.14

**预期结果**:
- ✅ 计算结果 = 3.14 (误差 < 0.01)
- ✅ 茅台流动比率应 > 2（健康水平）

**验证方法**:
```python
current_ratio = calculate_current_ratio('600519', 2024)
expected = 2200 / 700
assert abs(current_ratio - expected) < 0.01
assert current_ratio > 2
```

---

### 3.6 自由现金流计算准确性

**测试ID**: TC-CALC-006  
**优先级**: P0  
**计算公式**: `FCF = 经营现金流 - 资本支出`

**测试步骤**:
1. 使用贵州茅台 2024 年数据
2. 调用 `calculate_free_cash_flow(stock_code='600519', year=2024)`

**测试数据**:
- 经营现金流: 850 亿
- 资本支出: 150 亿（投资现金流绝对值）
- 预期 FCF: 700 亿

**预期结果**:
- ✅ 计算结果 = 700 亿 (误差 < 1%)

**验证方法**:
```python
fcf = calculate_free_cash_flow('600519', 2024)
expected = 850 - 150
assert abs(fcf - expected) / expected < 0.01
```

---

### 3.7 边界条件测试（除零、负值）

**测试ID**: TC-CALC-007  
**优先级**: P1  

**测试场景**:

#### 3.7.1 所有者权益为零
```python
# 当所有者权益为 0 时，ROE 应返回 None 或抛出异常
data = {'net_profit': 100, 'owners_equity': 0}
result = calculate_roe(data)
assert result is None or raises(ZeroDivisionError)
```

#### 3.7.2 总资产为零
```python
# 当总资产为 0 时，ROA 应返回 None
data = {'net_profit': 100, 'total_assets': 0}
result = calculate_roa(data)
assert result is None
```

#### 3.7.3 营业收入为零
```python
# 当营业收入为 0 时，毛利率应返回 None
data = {'revenue': 0, 'costs': 100}
result = calculate_gross_margin(data)
assert result is None
```

#### 3.7.4 净利润为负
```python
# 当净利润为负时，ROE 应为负数
data = {'net_profit': -100, 'equity': 1000}
result = calculate_roe(data)
assert result < 0
```

**预期结果**:
- ✅ 除零情况返回 None 或抛出明确异常
- ✅ 负值情况正常计算
- ✅ 日志记录异常情况

---

## 4️⃣ 异常检测测试

### 4.1 异常值检测（Z-score）

**测试ID**: TC-ANOMALY-001  
**优先级**: P1  
**检测方法**: Z-score > 3 视为异常

**测试步骤**:
1. 准备包含异常值的数据集
2. 调用 `detect_anomalies_zscore(data, threshold=3)`
3. 验证检测结果

**测试数据**:
```json
[
  {"year": 2020, "revenue": 1000},
  {"year": 2021, "revenue": 1050},
  {"year": 2022, "revenue": 1020},
  {"year": 2023, "revenue": 1080},
  {"year": 2024, "revenue": 5000}  // 异常值
]
```

**预期结果**:
- ✅ 检测到 2024 年数据为异常值
- ✅ 返回 Z-score > 3
- ✅ 标记为 `anomaly`

**验证方法**:
```python
anomalies = detect_anomalies_zscore(data, threshold=3)
assert len(anomalies) == 1
assert anomalies[0]['year'] == 2024
assert anomalies[0]['z_score'] > 3
```

---

### 4.2 缺失数据检测

**测试ID**: TC-ANOMALY-002  
**优先级**: P1  

**测试步骤**:
1. 准备缺失某个季度的数据集
2. 调用 `detect_missing_data(stock_code='600522', start_date='2024-01-01', end_date='2024-12-31')`

**测试数据**:
- 预期报告: 2024-Q1, Q2, Q3, Q4
- 实际报告: 2024-Q1, Q3, Q4（缺少 Q2）

**预期结果**:
- ✅ 检测到缺失 2024-Q2
- ✅ 返回缺失期间列表
- ✅ 标记为 `missing_data`

**验证方法**:
```python
missing = detect_missing_data('600522', '2024-01-01', '2024-12-31')
assert '2024-Q2' in missing
assert len(missing) == 1
```

---

### 4.3 负值检测

**测试ID**: TC-ANOMALY-003  
**优先级**: P1  

**测试步骤**:
1. 准备包含负值的数据
2. 调用 `detect_negative_values(data)`

**测试数据**:
- 总资产: 1000亿
- 所有者权益: -50亿（异常）

**预期结果**:
- ✅ 检测到负值所有者权益
- ✅ 返回异常字段列表
- ✅ 标记为 `negative_value`

**验证方法**:
```python
anomalies = detect_negative_values(data)
assert 'owners_equity' in anomalies['negative_fields']
assert anomalies['severity'] == 'high'
```

---

### 4.4 数据一致性检查

**测试ID**: TC-ANOMALY-004  
**优先级**: P1  

**测试步骤**:
1. 准备资产负债表数据
2. 验证会计恒等式: `总资产 = 总负债 + 所有者权益`

**测试数据**:
- 总资产: 2750亿
- 总负债: 750亿
- 所有者权益: 2000亿
- ✅ 一致

**异常数据**:
- 总资产: 2750亿
- 总负债: 750亿
- 所有者权益: 2100亿
- ❌ 不一致（2750 ≠ 750 + 2100）

**预期结果**:
- ✅ 正常数据通过检查
- ✅ 异常数据被检测到
- ✅ 返回差异值

**验证方法**:
```python
# 正常数据
result1 = check_balance_consistency(normal_data)
assert result1['is_consistent'] == True

# 异常数据
result2 = check_balance_consistency(anomaly_data)
assert result2['is_consistent'] == False
assert result2['difference'] == 100  # 差异100亿
```

---

## 5️⃣ 性能测试

### 5.1 单只股票查询性能

**测试ID**: TC-PERF-001  
**优先级**: P0  
**性能指标**: < 1秒

**测试步骤**:
1. 调用 `get_financial_data(stock_code='600519')`
2. 记录响应时间
3. 重复 10 次取平均值

**预期结果**:
- ✅ 平均响应时间 < 1s
- ✅ 95 分位 < 1.5s
- ✅ 无超时错误

**验证方法**:
```python
import time
times = []
for i in range(10):
    start = time.time()
    get_financial_data('600519')
    end = time.time()
    times.append(end - start)

avg_time = sum(times) / len(times)
p95 = sorted(times)[int(len(times) * 0.95)]
assert avg_time < 1.0
assert p95 < 1.5
```

---

### 5.2 批量查询 100 只股票性能

**测试ID**: TC-PERF-002  
**优先级**: P1  
**性能指标**: < 30秒

**测试步骤**:
1. 准备 100 只股票代码列表
2. 调用 `batch_get_financial_data(stock_codes)`
3. 记录总耗时

**预期结果**:
- ✅ 总耗时 < 30s
- ✅ 平均每只股票 < 0.3s
- ✅ 失败率 < 5%

**验证方法**:
```python
stock_codes = load_test_stocks(100)  # 从测试数据加载
start = time.time()
results = batch_get_financial_data(stock_codes)
end = time.time()

assert (end - start) < 30
assert results['success_rate'] > 0.95
```

---

### 5.3 数据库查询性能

**测试ID**: TC-PERF-003  
**优先级**: P1  
**性能指标**: < 100ms

**测试步骤**:
1. 执行数据库查询: `SELECT * FROM financial_data WHERE stock_code='600519' AND year=2024`
2. 记录查询时间
3. 重复 100 次取平均值

**预期结果**:
- ✅ 平均查询时间 < 100ms
- ✅ 95 分位 < 150ms
- ✅ 使用索引优化

**验证方法**:
```python
import time
query_times = []
for i in range(100):
    start = time.time()
    db.execute("SELECT * FROM financial_data WHERE stock_code='600519' AND year=2024")
    end = time.time()
    query_times.append((end - start) * 1000)  # 转换为毫秒

avg_query_time = sum(query_times) / len(query_times)
assert avg_query_time < 100
```

---

## 6️⃣ 集成测试

### 6.1 完整流程测试

**测试ID**: TC-INT-001  
**优先级**: P0  

**测试步骤**:
1. 获取财务数据（Tushare）
2. 存储到数据库
3. 计算财务指标
4. 异常检测
5. 返回分析结果

**预期结果**:
- ✅ 每个步骤成功
- ✅ 数据流转正确
- ✅ 总耗时 < 5s

**验证方法**:
```python
# 完整流程
data = fetch_financial_data('600519')
save_result = save_to_database(data)
indicators = calculate_indicators(data)
anomalies = detect_anomalies(data)
report = generate_report(indicators, anomalies)

assert save_result['status'] == 'success'
assert 'roe' in indicators
assert report is not None
```

---

## 7️⃣ 错误处理测试

### 7.1 无效股票代码

**测试ID**: TC-ERR-001  
**优先级**: P1  

**测试步骤**:
1. 使用无效股票代码: `999999`, `123456789`, `ABC123`, `""`
2. 调用 `get_financial_data(stock_code)`

**预期结果**:
- ✅ 返回 HTTP 400
- ✅ 错误信息: "Invalid stock code"
- ✅ 不崩溃

**验证方法**:
```python
invalid_codes = ['999999', '123456789', 'ABC123', '']
for code in invalid_codes:
    result = get_financial_data(code)
    assert result.status_code == 400
    assert 'invalid' in result.json()['error'].lower()
```

---

### 7.2 API 频率限制

**测试ID**: TC-ERR-002  
**优先级**: P2  

**测试步骤**:
1. 短时间内发送大量请求（> 100 次/分钟）
2. 验证系统处理

**预期结果**:
- ✅ 返回 HTTP 429
- ✅ 包含 Retry-After 头
- ✅ 记录限流日志

**验证方法**:
```python
# 并发请求测试
results = []
for i in range(150):
    result = get_financial_data('600519')
    results.append(result.status_code)

assert 429 in results
assert 'retry-after' in response.headers
```

---

## 8️⃣ 数据质量测试

### 8.1 数据完整性

**测试ID**: TC-QUALITY-001  
**优先级**: P1  

**验证项目**:
- ✅ 必填字段无缺失
- ✅ 数据类型正确
- ✅ 数值范围合理
- ✅ 日期格式统一

**验证方法**:
```python
required_fields = ['stock_code', 'report_date', 'total_assets', 'total_liabilities']
data = get_financial_data('600519')

for field in required_fields:
    assert field in data
    assert data[field] is not None

# 数值范围检查
assert data['total_assets'] > 0
assert data['total_liabilities'] >= 0
```

---

## 9️⃣ 测试执行计划

### 测试执行顺序
1. **单元测试** (Day 1)
   - 财务指标计算测试 (TC-CALC-*)
   - 异常检测测试 (TC-ANOMALY-*)

2. **集成测试** (Day 2)
   - 数据获取测试 (TC-FETCH-*)
   - 数据存储测试 (TC-STORE-*)

3. **性能测试** (Day 3)
   - 单只股票查询 (TC-PERF-001)
   - 批量查询 (TC-PERF-002)
   - 数据库查询 (TC-PERF-003)

4. **端到端测试** (Day 4)
   - 完整流程测试 (TC-INT-001)
   - 错误处理测试 (TC-ERR-*)

### 测试环境要求
- Python 3.9+
- PostgreSQL 13+
- Tushare Pro API Token
- AkShare 已安装
- 测试数据库（独立环境）

### 测试数据准备
1. 运行 `python scripts/init_test_db.py` 初始化测试数据库
2. 运行 `python scripts/load_test_data.py` 加载测试数据
3. 验证数据完整性

---

## 🔟 测试报告模板

### 测试摘要
- **测试日期**: YYYY-MM-DD
- **测试人员**: @tester
- **总用例数**: XX
- **通过数**: XX
- **失败数**: XX
- **阻塞数**: XX
- **通过率**: XX%

### 缺陷统计
| 严重级别 | 数量 | 描述 |
|---------|------|------|
| P0 - 阻塞 | X | XXX |
| P1 - 严重 | X | XXX |
| P2 - 一般 | X | XXX |
| P3 - 轻微 | X | XXX |

### 性能测试结果
| 测试项 | 目标 | 实际 | 结果 |
|--------|------|------|------|
| 单只股票查询 | < 1s | X.Xs | ✅/❌ |
| 批量查询 100 只 | < 30s | XXs | ✅/❌ |
| 数据库查询 | < 100ms | XXms | ✅/❌ |

---

## 📝 附录

### A. 测试数据说明
详见 `week4_test_data.json`

### B. 验证数据来源
详见 `week4_validation_data.json`

### C. 自动化测试脚本
```bash
# 运行所有测试
pytest tests/week4/ -v

# 运行特定测试
pytest tests/week4/test_fetch.py::TC_FETCH_001 -v

# 生成覆盖率报告
pytest tests/week4/ --cov=src --cov-report=html
```

---

**文档版本**: v1.0  
**最后更新**: 2026-03-22  
**维护者**: @tester
