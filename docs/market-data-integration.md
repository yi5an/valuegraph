# ValueGraph 市场数据集成文档

**集成日期**: 2026-03-25  
**状态**: ✅ 已完成

---

## 📊 数据源调研

### 1. EMQ 极速行情
- **状态**: ⏸️ 暂停
- **原因**: 需要 SDK 文档
- **支持市场**: 仅 A股
- **备注**: 付费方案，待文档后继续评估

### 2. Finnhub
- **状态**: ✅ 免费版可用
- **支持市场**: 美股、港股
- **API Key**: 已配置 (`.env: FINNHUB_API_KEY`)
- **限制**: 60 calls/min
- **文档**: https://finnhub.io/docs/api

### 3. akshare
- **状态**: ⚠️ 部分可用
- **支持市场**: 仅 A股
- **优势**: 历史数据稳定
- **劣势**: 实时数据不稳定

### 4. Ashare ⭐
- **状态**: ✅ 推荐
- **支持市场**: 仅 A股
- **优势**: 
  - 新浪/腾讯双核心数据源
  - 稳定性高
  - 免费使用
- **GitHub**: https://github.com/mpquant/Ashare

---

## 🔧 集成工作

### 复制文件
```
backend/app/services/
├── Ashare.py     # A股数据源
├── MyTT.py       # 技术指标库
└── market_data.py # 统一市场数据接口
```

### 新建文件
- **`market_data.py`** - 统一市场数据接口
  - `get_stock_quote()` - 获取股票报价
  - `get_stock_daily()` - 获取日线数据
  - `get_stock_minute()` - 获取分钟线数据
  - `get_company_profile()` - 获取公司简介

### 配置文件
**`.env`** 添加:
```bash
FINNHUB_API_KEY=d71oughr01qpd278nlpgd71oughr01qpd278nlq0
```

---

## ✅ 测试结果

### A股日线数据
```python
# 平安银行 (000001.SZ)
get_stock_daily("000001", market="A股", start_date="2026-01-01")
# ✅ 成功
```

### A股分钟线数据
```python
# 贵州茅台 (600519.SH)
get_stock_minute("600519", market="A股")
# ✅ 成功
```

### 美股报价
```python
# 苹果 (AAPL)
get_stock_quote("AAPL", market="美股")
# ✅ 成功 - $251.64
```

### 美股公司简介
```python
# 苹果 (AAPL)
get_company_profile("AAPL")
# ✅ 成功
```

---

## 🎯 数据源分工

| 市场 | 数据源 | 优先级 | 说明 |
|------|--------|--------|------|
| **A股** | Ashare | P0 | 新浪/腾讯双核心，稳定可靠 |
| **美股** | Finnhub | P0 | 免费版，功能完整 |
| **港股** | Finnhub | P0 | 免费版，功能完整 |
| A股(备用) | akshare | P1 | 仅历史数据 |
| A股(付费) | EMQ 极速行情 | P2 | 待 SDK 文档 |

---

## 📝 使用示例

### 获取 A股数据
```python
from app.services.market_data import get_stock_quote, get_stock_daily

# 获取实时报价
quote = get_stock_quote("000001", market="A股")

# 获取日线数据
daily = get_stock_daily("000001", market="A股", start_date="2026-01-01")
```

### 获取美股数据
```python
from app.services.market_data import get_stock_quote, get_company_profile

# 获取实时报价
quote = get_stock_quote("AAPL", market="美股")

# 获取公司简介
profile = get_company_profile("AAPL")
```

---

## ⚠️ 注意事项

1. **Finnhub 限制**: 免费版 60 calls/min，需注意频率控制
2. **Ashare 数据源**: 新浪/腾讯双核心，自动切换故障源
3. **市场代码格式**:
   - A股: 6位代码（如 000001）
   - 美股: 股票符号（如 AAPL）
   - 港股: 数字代码（如 00700）

---

## 📚 相关文档

- [ValueGraph PRD](./valuegraph-prd.md)
- [Finnhub API 文档](https://finnhub.io/docs/api)
- [Ashare GitHub](https://github.com/mpquant/Ashare)

---

**维护者**: OpenClaw Agent Team  
**最后更新**: 2026-03-25
