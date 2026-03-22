# ValueGraph - AkShare 集成说明

## 快速开始

### 1. 环境要求
- Python 3.9+ (推荐使用 Anaconda)
- AkShare 1.18.43+

### 2. 安装依赖
```bash
cd ~/valuegraph/backend
pip install -r requirements.txt
```

### 3. 启动服务
```bash
cd ~/valuegraph
./start_backend.sh
```

服务将在 `http://localhost:8000` 启动

### 4. 访问 API 文档
打开浏览器访问：`http://localhost:8000/docs`

## API 接口

### 1. 获取推荐股票
```http
GET /api/stocks/recommend?market=a-share&top_n=10&min_roe=15&max_debt_ratio=50
```

参数说明：
- `market`: 市场类型（默认：a-share）
- `top_n`: 返回数量（默认：10，范围：1-50）
- `min_roe`: 最低 ROE 要求（默认：15%）
- `max_debt_ratio`: 最高负债率要求（默认：50%）

响应示例：
```json
{
  "success": true,
  "market": "a-share",
  "count": 5,
  "filters": {
    "min_roe": 15.0,
    "max_debt_ratio": 50.0
  },
  "data": [
    {
      "代码": "600519",
      "名称": "贵州茅台",
      "roe": 25.5,
      "debt_ratio": 30.2,
      "score": 77.65
    }
  ]
}
```

### 2. 获取股票详情
```http
GET /api/stocks/{stock_code}
```

响应示例：
```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "financial_data": {
      "roe": 25.5,
      "debt_ratio": 30.2
    },
    "shareholders": [
      {
        "股东名称": "中国贵州茅台酒厂(集团)有限责任公司",
        "持股数量": 678000000,
        "持股比例": 54.06
      }
    ]
  }
}
```

### 3. 健康检查
```http
GET /api/health
GET /api/stocks/health/check
```

## 测试

### 测试 AkShare API
```bash
cd ~/valuegraph
python test_akshare_simple.py
```

### 测试 REST API
```bash
cd ~/valuegraph
./test_api.sh
```

## 项目结构

```
valuegraph/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 主应用
│   │   ├── routers/
│   │   │   └── stocks.py        # 股票相关 API 路由
│   │   └── services/
│   │       ├── data_source.py      # 数据源抽象基类
│   │       ├── akshare_adapter.py  # AkShare 适配器
│   │       └── stock_service.py    # 股票业务逻辑
│   └── requirements.txt
├── test_akshare_simple.py       # AkShare 测试脚本
├── test_api.sh                  # API 测试脚本
├── start_backend.sh             # 启动脚本
└── AKSHARE_INTEGRATION_REPORT.md # 集成报告
```

## 已知问题

1. **网络依赖**：AkShare 需要访问外部 API，可能受网络影响
2. **财务数据**：部分 API 返回空数据，需要进一步调查
3. **并发限制**：为避免频率限制，限制了并发数量

## 下一步计划

- [ ] 添加 Redis 缓存
- [ ] 修复财务数据获取问题
- [ ] 添加更多筛选条件
- [ ] 添加单元测试
- [ ] 添加日志系统

## 联系方式

如有问题，请在 Telegram 群组联系。
