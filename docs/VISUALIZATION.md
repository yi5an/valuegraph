# 可视化组件说明文档

**版本**：v0.3.0  
**更新日期**：2026-03-22  
**作者**：Documenter

---

## 📊 图表组件概览

Week 5 新增了 4 个可视化组件，用于展示财务数据的时间线变化和综合分析。

### 组件列表

| 组件名称 | 功能 | 图表类型 | 适用场景 |
|---------|------|---------|---------|
| FinancialChart | 时间线图表 | 折线图 | 展示财务指标的历史趋势 |
| MultiMetricComparison | 多指标对比 | 多折线图 | 对比不同指标的变化趋势 |
| FinancialRadar | 财务雷达图 | 雷达图 | 综合展示财务健康度 |
| DuPontTree | 杜邦分析树 | 树形图 | 展示 ROE 的分解结构 |

---

## 🎨 设计规范

### 1. 配色方案

#### 主色调
```
- 主色（Primary）：#1890ff（蓝色）
- 成功色（Success）：#52c41a（绿色）
- 警告色（Warning）：#faad14（橙色）
- 错误色（Error）：#ff4d4f（红色）
```

#### 图表配色
```
- ROE：#5470c6（蓝色）
- ROA：#91cc75（绿色）
- 负债率：#fac858（黄色）
- 收入：#ee6666（红色）
- 净利润：#73c0de（浅蓝）
- 毛利率：#3ba272（深绿）
- 流动比率：#fc8452（橙色）
- 自由现金流：#9a60b4（紫色）
```

#### 使用原则
- **一致性**：相同指标在不同图表中使用相同颜色
- **对比度**：确保颜色之间有足够的对比度
- **色盲友好**：避免仅依赖颜色区分，配合形状和标签
- **语义化**：绿色表示正向指标，红色表示负向指标

---

### 2. 交互设计规范

#### 通用交互
- **悬停效果**：显示详细数据 tooltip
- **点击图例**：切换指标的显示/隐藏
- **缩放拖动**：支持 dataZoom 组件
- **响应式**：自适应不同屏幕尺寸

#### FinancialChart 交互
```typescript
// 1. 鼠标悬停
tooltip: {
  trigger: 'axis',
  axisPointer: { type: 'cross' },
  formatter: (params) => {
    // 格式化显示
    return `${params[0].axisValue}<br/>
            ${params.map(p => `${p.marker} ${p.seriesName}: ${p.value}`).join('<br/>')}`
  }
}

// 2. 图例交互
legend: {
  data: metrics,
  type: 'scroll',  // 可滚动图例
  selected: {}     // 控制显示/隐藏
}

// 3. 缩放拖动
dataZoom: [
  { type: 'inside', start: 0, end: 100 },
  { type: 'slider', start: 0, end: 100 }
]
```

#### MultiMetricComparison 交互
```typescript
// 下拉框多选
<Select
  mode="multiple"
  style={{ width: '100%' }}
  value={selectedMetrics}
  onChange={setSelectedMetrics}
  options={metricOptions}
  placeholder="选择要对比的指标"
/>
```

#### FinancialRadar 交互
```typescript
// 悬停显示实际值
tooltip: {
  trigger: 'item',
  formatter: (params) => {
    return `${params.name}<br/>
            ROE: ${actualData.roe}%<br/>
            ROA: ${actualData.roa}%<br/>
            毛利率: ${actualData.grossMargin}%<br/>
            流动比率: ${actualData.currentRatio}<br/>
            自由现金流: ${formatCurrency(actualData.freeCashFlow)}`
  }
}
```

---

### 3. 响应式设计

#### 断点设置
```typescript
// Ant Design Grid 系统
xs: < 576px   (手机)
sm: ≥ 576px   (小平板)
md: ≥ 768px   (平板)
lg: ≥ 992px   (桌面)
xl: ≥ 1200px  (大屏)
xxl: ≥ 1600px (超大屏)
```

#### 布局示例
```typescript
<Row gutter={[16, 16]}>
  {/* 手机：全宽，桌面：半宽 */}
  <Col xs={24} lg={12}>
    <FinancialRadar metrics={radarData} />
  </Col>
  <Col xs={24} lg={12}>
    <DuPontTree data={duPontData} />
  </Col>
  
  {/* 全宽 */}
  <Col xs={24}>
    <FinancialChart stockCode="600519" />
  </Col>
</Row>
```

#### 图表自适应
```typescript
// ECharts 自适应
useEffect(() => {
  const handleResize = () => {
    if (chartRef.current) {
      chartRef.current.resize()
    }
  }
  
  window.addEventListener('resize', handleResize)
  return () => window.removeEventListener('resize', handleResize)
}, [])
```

---

## 📈 组件详细说明

### 1. FinancialChart - 时间线图表

#### 功能描述
展示财务指标在 5-10 年间的变化趋势，支持多指标对比、缩放拖动。

#### 技术实现
```typescript
import ReactECharts from 'echarts-for-react'

const FinancialChart: React.FC<Props> = ({ stockCode, metrics, years }) => {
  const option = {
    title: { text: '财务指标趋势' },
    tooltip: { trigger: 'axis' },
    legend: { data: metrics },
    xAxis: { type: 'category', data: years },
    yAxis: { type: 'value' },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider' }
    ],
    series: metrics.map(metric => ({
      name: metric,
      type: 'line',
      data: data[metric],
      smooth: true
    }))
  }
  
  return <ReactECharts option={option} />
}
```

#### 配置项
- `smooth: true` - 平滑曲线
- `symbol: 'circle'` - 数据点形状
- `symbolSize: 8` - 数据点大小
- `lineStyle.width: 2` - 线宽

---

### 2. MultiMetricComparison - 多指标对比

#### 功能描述
通过下拉框选择多个指标，实时更新图表进行对比分析。

#### 技术实现
```typescript
import { Select } from 'antd'
import ReactECharts from 'echarts-for-react'

const MultiMetricComparison: React.FC<Props> = ({ stockCode }) => {
  const [selectedMetrics, setSelectedMetrics] = useState(['roe', 'roa'])
  
  const metricOptions = [
    { label: 'ROE', value: 'roe' },
    { label: 'ROA', value: 'roa' },
    { label: '负债率', value: 'debt_ratio' },
    // ... 其他指标
  ]
  
  return (
    <>
      <Select
        mode="multiple"
        value={selectedMetrics}
        onChange={setSelectedMetrics}
        options={metricOptions}
      />
      <ReactECharts option={getChartOption(selectedMetrics)} />
    </>
  )
}
```

#### 默认指标
- ROE（净资产收益率）
- ROA（总资产收益率）
- 毛利率

---

### 3. FinancialRadar - 财务雷达图

#### 功能描述
综合展示 5 个维度的财务健康度指标。

#### 技术实现
```typescript
const FinancialRadar: React.FC<Props> = ({ metrics }) => {
  // 数据归一化到 0-100
  const normalizeValue = (value: number, max: number) => {
    return (value / max) * 100
  }
  
  const option = {
    title: { text: '财务健康度分析' },
    radar: {
      indicator: [
        { name: 'ROE', max: 100 },
        { name: 'ROA', max: 100 },
        { name: '毛利率', max: 100 },
        { name: '流动比率', max: 100 },
        { name: '自由现金流', max: 100 }
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          normalizeValue(metrics.roe, 50),
          normalizeValue(metrics.roa, 30),
          normalizeValue(metrics.grossMargin, 80),
          normalizeValue(metrics.currentRatio, 5),
          normalizeValue(metrics.freeCashFlow, maxFCF)
        ],
        name: '当前值'
      }]
    }]
  }
  
  return <ReactECharts option={option} />
}
```

#### 归一化算法
```
归一化值 = (实际值 / 最大值) × 100

最大值设定：
- ROE: 50%
- ROA: 30%
- 毛利率: 80%
- 流动比率: 5
- 自由现金流: 根据行业设定
```

---

### 4. DuPontTree - 杜邦分析树

#### 功能描述
展示 ROE 的三层分解结构：ROE = 净利润率 × 资产周转率 × 权益乘数。

#### 技术实现
```typescript
import { Tree } from 'antd'

const DuPontTree: React.FC<Props> = ({ data }) => {
  const treeData = [
    {
      title: `ROE: ${data.roe}%`,
      key: 'roe',
      children: [
        { title: `净利润率: ${data.netProfitMargin}%`, key: 'npm' },
        { title: `资产周转率: ${data.assetTurnover}`, key: 'at' },
        { title: `权益乘数: ${data.equityMultiplier}`, key: 'em' }
      ]
    }
  ]
  
  return (
    <>
      <div className="mb-3 text-gray-600">
        ROE = 净利润率 × 资产周转率 × 权益乘数
      </div>
      <Tree
        treeData={treeData}
        defaultExpandAll
        showLine
      />
    </>
  )
}
```

#### 杜邦分析公式
```
ROE = 净利润 / 净资产
    = (净利润 / 营业收入) × (营业收入 / 总资产) × (总资产 / 净资产)
    = 净利润率 × 资产周转率 × 权益乘数
```

---

## 🎯 使用示例

### 完整页面示例
```typescript
import { Row, Col, Card } from 'antd'
import FinancialChart from '@/components/FinancialChart'
import MultiMetricComparison from '@/components/MultiMetricComparison'
import FinancialRadar from '@/components/FinancialRadar'
import DuPontTree from '@/components/DuPontTree'

const StockAnalysisPage: React.FC = () => {
  const stockCode = '600519'
  
  return (
    <div className="p-6">
      {/* 时间线图表 */}
      <Card title="财务趋势" className="mb-6">
        <FinancialChart
          stockCode={stockCode}
          metrics={['roe', 'roa', 'debt_ratio']}
          years={5}
        />
      </Card>
      
      {/* 多指标对比 */}
      <Card title="指标对比" className="mb-6">
        <MultiMetricComparison
          stockCode={stockCode}
          defaultMetrics={['roe', 'net_profit', 'revenue']}
          years={5}
        />
      </Card>
      
      {/* 雷达图 + 杜邦分析 */}
      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="财务健康度">
            <FinancialRadar metrics={radarData} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="杜邦分析">
            <DuPontTree data={duPontData} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
```

---

## ⚡ 性能优化

### 1. 数据缓存
```typescript
// 使用 useMemo 缓存计算结果
const chartData = useMemo(() => {
  return processData(rawData)
}, [rawData])

// 使用 React Query 缓存 API 请求
const { data } = useQuery(['financial', stockCode], () =>
  fetchFinancialData(stockCode), {
    staleTime: 5 * 60 * 1000, // 5 分钟
    cacheTime: 10 * 60 * 1000  // 10 分钟
  }
)
```

### 2. 懒加载
```typescript
// 使用 React.lazy 懒加载组件
const FinancialChart = React.lazy(() => import('@/components/FinancialChart'))

// 使用 Suspense 包裹
<Suspense fallback={<Spin />}>
  <FinancialChart {...props} />
</Suspense>
```

### 3. 按需加载 ECharts
```typescript
// 只加载需要的图表类型
import * as echarts from 'echarts/core'
import { LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'

echarts.use([
  LineChart,
  RadarChart,
  GridComponent,
  TooltipComponent
])
```

---

## 🐛 错误处理

### 1. API 失败降级
```typescript
try {
  const data = await fetchFinancialData(stockCode)
  setChartData(data)
} catch (error) {
  console.error('Failed to fetch financial data:', error)
  message.warning('使用模拟数据展示')
  setChartData(generateMockData())
}
```

### 2. 空数据处理
```typescript
if (!data || data.length === 0) {
  return (
    <Empty
      description="暂无数据"
      image={Empty.PRESENTED_IMAGE_SIMPLE}
    />
  )
}
```

### 3. 加载状态
```typescript
{loading ? (
  <Spin tip="加载中...">
    <div style={{ height: 400 }} />
  </Spin>
) : (
  <ReactECharts option={option} />
)}
```

---

## 📱 移动端适配

### 响应式布局
- 手机：全宽显示，单列布局
- 平板：半宽显示，双列布局
- 桌面：半宽或全宽，根据内容调整

### 触摸操作
- 支持单指拖动
- 支持双指缩放
- 图例可点击

### 字体大小
```css
/* 移动端 */
@media (max-width: 768px) {
  .chart-title {
    font-size: 16px;
  }
  .chart-label {
    font-size: 12px;
  }
}

/* 桌面端 */
@media (min-width: 769px) {
  .chart-title {
    font-size: 18px;
  }
  .chart-label {
    font-size: 14px;
  }
}
```

---

## 🧪 测试覆盖

### 单元测试
```typescript
describe('FinancialChart', () => {
  it('should render chart with data', () => {
    render(<FinancialChart stockCode="600519" metrics={['roe']} />)
    expect(screen.getByText('财务指标趋势')).toBeInTheDocument()
  })
  
  it('should show loading state', () => {
    render(<FinancialChart loading={true} />)
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })
})
```

### E2E 测试（建议）
```typescript
// 使用 Playwright
test('chart interaction', async ({ page }) => {
  await page.goto('/stock/600519')
  await page.hover('.echarts-for-react')
  await expect(page.locator('.tooltip')).toBeVisible()
})
```

---

## 📚 参考资料

- [ECharts 文档](https://echarts.apache.org/zh/index.html)
- [Ant Design 组件库](https://ant.design/components/overview-cn/)
- [echarts-for-react](https://github.com/hustcc/echarts-for-react)
- [杜邦分析法](https://wiki.mbalib.com/wiki/杜邦分析法)

---

## 📝 更新日志

### v0.3.0 (2026-03-22)
- ✅ 新增 FinancialChart 组件
- ✅ 新增 MultiMetricComparison 组件
- ✅ 新增 FinancialRadar 组件
- ✅ 新增 DuPontTree 组件
- ✅ 实现响应式设计
- ✅ 实现错误降级处理
- ✅ 完成代码审查

---

**文档维护**：Documenter  
**最后更新**：2026-03-22 23:50
