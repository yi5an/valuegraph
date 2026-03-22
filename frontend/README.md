# ValueGraph Frontend

价值投资知识图谱平台 - 前端项目

## 技术栈

- **框架**: Next.js 16.2.1 (App Router)
- **UI 库**: React 19.2.4
- **语言**: TypeScript 5
- **样式**: TailwindCSS 4
- **组件库**: Ant Design 5
- **图表库**: ECharts 5

## 项目结构

```
frontend/
├── app/                    # Next.js App Router
│   ├── api/               # API 路由
│   │   └── proxy/         # API 代理
│   ├── stocks/            # 股票详情页
│   │   └── [code]/        # 动态路由
│   ├── layout.tsx         # 全局布局
│   └── page.tsx           # 首页
├── components/            # 组件目录
│   ├── FinancialChart.tsx # 财报图表
│   ├── MarketTabs.tsx     # 市场切换
│   ├── ShareholderTable.tsx # 股东表格
│   └── StockCard.tsx      # 股票卡片
├── lib/                   # 工具库
│   └── api.ts             # API 封装
└── styles/                # 样式文件
    └── globals.css        # 全局样式
```

## 功能特性

### MVP 功能

1. **多市场价值投资推荐**
   - A股市场切换
   - 美股市场切换
   - 股票卡片展示

2. **财报深度分析**
   - 时间线图表
   - 营业收入趋势
   - 净利润走势
   - ROE 变化

3. **持股信息查询**
   - 股东列表表格
   - 持股比例展示
   - 持股变化追踪

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3001

### 构建生产版本

```bash
npm run build
npm start
```

## 环境变量

创建 `.env.local` 文件：

```env
# 后端 API 地址
BACKEND_URL=http://localhost:8000

# 公开 API URL（前端使用）
NEXT_PUBLIC_API_URL=/api/proxy
```

## API 接口

前端通过 `/api/proxy` 代理访问后端 API：

- `GET /api/proxy?path=/stocks?market=a-share` - 获取股票列表
- `GET /api/proxy?path=/stocks/:code` - 获取股票详情
- `GET /api/proxy?path=/stocks/:code/financials` - 获取财报数据
- `GET /api/proxy?path=/stocks/:code/shareholders` - 获取股东信息

## 协作

- **后端**: 需要在 `http://localhost:8000` 提供以上 API 接口
- **设计**: UI 设计需与 @designer 对齐

## 状态

✅ 项目初始化完成
✅ 基础组件创建完成
✅ API 代理配置完成
✅ 开发服务器可运行

## 下一步

- [ ] 对接真实后端 API
- [ ] 添加更多财务指标
- [ ] 实现数据筛选和排序
- [ ] 添加用户收藏功能
- [ ] 优化移动端体验
