# Week 4 测试文件说明

## 📁 文件清单

### 1. week4_test_data.json (15KB)
**用途**: 测试数据集  
**内容**:
- 贵州茅台（600519）2015-2024 年财务数据
  - 资产负债表（正常数据 + 边界条件 + 异常数据）
  - 利润表（正常数据 + 边界条件）
  - 现金流量表（正常数据 + 边界条件）
- 预期财务指标计算结果
- 异常场景数据（ROE骤降、负利润、缺失数据等）
- 性能测试数据（20只股票批量查询）
- 错误处理场景

**使用方式**:
```python
import json
with open('week4_test_data.json', 'r') as f:
    test_data = json.load(f)
    
# 获取资产负债表测试数据
balance_sheets = test_data['balance_sheets']['normal_data']

# 获取异常场景
anomaly_scenarios = test_data['anomaly_scenarios']
```

---

### 2. week4_test_cases.md (22KB)
**用途**: 详细测试用例文档  
**内容**:
- **1️⃣ 财务数据获取测试** (5 个用例)
  - 获取资产负债表、利润表、现金流量表
  - 数据源降级测试
  - 网络异常处理

- **2️⃣ 数据存储测试** (5 个用例)
  - 存储各类财务报表
  - 重复数据检测
  - 批量存储性能

- **3️⃣ 财务指标计算测试** (7 个用例)
  - ROE、ROA、资产负债率、毛利率、流动比率、自由现金流
  - 边界条件测试（除零、负值）

- **4️⃣ 异常检测测试** (4 个用例)
  - Z-score 异常值检测
  - 缺失数据检测
  - 负值检测
  - 数据一致性检查

- **5️⃣ 性能测试** (3 个用例)
  - 单只股票查询 < 1s
  - 批量查询 100 只股票 < 30s
  - 数据库查询 < 100ms

- **6️⃣ 集成测试** (1 个用例)
  - 完整流程测试

- **7️⃣ 错误处理测试** (2 个用例)
  - 无效股票代码
  - API 频率限制

- **8️⃣ 数据质量测试** (1 个用例)
  - 数据完整性验证

**测试用例总数**: 28 个

**使用方式**:
按照文档中的测试步骤执行测试，每个用例包含：
- 测试ID和优先级
- 前置条件
- 测试步骤
- 预期结果
- 验证方法（含代码示例）

---

### 3. week4_validation_data.json (25KB)
**用途**: 验证数据和基准数据  
**内容**:
- **历史财务数据** (2019-2024 年度报告)
  - 资产负债表
  - 利润表
  - 现金流量表
  - 数据来源：东方财富、同花顺

- **预期财务指标**
  - ROE、ROA、资产负债率、毛利率、流动比率、自由现金流
  - 包含计算公式、预期值、允许误差
  - 2019-2024 年完整数据

- **行业基准**
  - 白酒行业财务指标标准
  - 优秀/良好/较差分级

- **异常案例** (8 个案例)
  - ROE 骤降
  - 负净利润
  - 数据缺失
  - 会计恒等式不成立
  - 财务数据剧烈波动
  - 超高负债率
  - 负所有者权益
  - 现金流异常

- **数据质量检查规则**
  - 完整性检查
  - 准确性检查
  - 一致性检查
  - 时效性检查

- **对比数据源**
  - 东方财富 Choice
  - 同花顺 iFinD
  - Wind 金融终端
  - 巨潮资讯网

- **验证流程**
  - 5 步验证程序
  - 通过标准

- **测试场景** (4 个综合场景)
  - 正常数据验证
  - 异常数据检测
  - 数据一致性验证
  - 行业对比分析

**使用方式**:
```python
import json
with open('week4_validation_data.json', 'r') as f:
    validation_data = json.load(f)

# 获取 2024 年预期财务指标
expected_indicators = validation_data['expected_indicators']['2024']

# 验证 ROE
system_roe = calculate_roe('600519', 2024)
expected_roe = expected_indicators['roe']['expected_value']
tolerance = expected_indicators['roe']['tolerance']

assert abs(system_roe - expected_roe) < tolerance
```

---

## 🚀 快速开始

### 1. 加载测试数据
```bash
cd /home/yi5an/.openclaw/workspace/projects/valuegraph/tests
python -c "import json; print(json.load(open('week4_test_data.json'))['test_data_info'])"
```

### 2. 查看测试用例
```bash
cat week4_test_cases.md | grep "测试ID"
```

### 3. 验证数据完整性
```bash
python << EOF
import json

# 验证测试数据
with open('week4_test_data.json') as f:
    test_data = json.load(f)
    print(f"✅ 资产负债表数据: {len(test_data['balance_sheets']['normal_data'])} 条")
    print(f"✅ 利润表数据: {len(test_data['income_statements']['normal_data'])} 条")
    print(f"✅ 现金流量表数据: {len(test_data['cash_flow_statements']['normal_data'])} 条")

# 验证验证数据
with open('week4_validation_data.json') as f:
    validation_data = json.load(f)
    print(f"✅ 历史数据年份: {len(validation_data['historical_financial_data'])} 年")
    print(f"✅ 异常案例: {len(validation_data['anomaly_cases'])} 个")
    print(f"✅ 测试场景: {len(validation_data['test_scenarios'])} 个")
EOF
```

---

## 📊 测试覆盖范围

| 测试类型 | 用例数 | 覆盖率 |
|---------|--------|--------|
| 数据获取 | 5 | 核心功能 100% |
| 数据存储 | 5 | 核心功能 100% |
| 指标计算 | 7 | 核心指标 100% |
| 异常检测 | 4 | 主要场景 100% |
| 性能测试 | 3 | 关键指标 100% |
| **总计** | **28** | **核心功能 100%** |

---

## ⚠️ 注意事项

1. **数据来源**: 测试数据基于贵州茅台真实财务规律，但为模拟数据
2. **实际测试**: 等待 @coder 完成 Week 4 开发后执行
3. **数据更新**: 实际测试时应从 Tushare/AkShare 获取最新数据
4. **误差范围**: 财务指标计算误差应 < 1%
5. **性能指标**: 必须满足性能测试要求

---

## 📝 测试执行建议

### Day 1: 单元测试
- 执行 TC-CALC-* (财务指标计算)
- 执行 TC-ANOMALY-* (异常检测)

### Day 2: 集成测试
- 执行 TC-FETCH-* (数据获取)
- 执行 TC-STORE-* (数据存储)

### Day 3: 性能测试
- 执行 TC-PERF-* (性能测试)

### Day 4: 端到端测试
- 执行 TC-INT-* (集成测试)
- 执行 TC-ERR-* (错误处理)

---

## 📞 联系方式

**测试工程师**: @tester  
**创建日期**: 2026-03-22  
**版本**: v1.0  
**状态**: ✅ 已完成，等待开发完成

---

## 🎯 成功标准

- ✅ 所有 P0 测试用例通过
- ✅ 95% 以上测试用例通过
- ✅ 性能指标达标
- ✅ 无 P0 级别缺陷
- ✅ 财务指标计算误差 < 1%

**准备好开始测试了！** 🚀
