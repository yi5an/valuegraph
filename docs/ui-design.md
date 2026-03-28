# ValueGraph 前端 UI 设计规范

> 价值投资知识图谱平台 · 专业 · 简洁 · 数据驱动

---

## 📋 目录

1. [整体布局](#整体布局)
2. [页面设计](#页面设计)
   - [价值推荐页（首页）](#1-价值推荐页首页)
   - [财报分析页](#2-财报分析页)
   - [持股查询页](#3-持股查询页)
3. [配色方案](#配色方案)
4. [组件规范](#组件规范)

---

## 整体布局

### 布局架构

采用 **Dashboard Layout（仪表盘布局）**，适合数据密集型金融产品：

```
┌─────────────────────────────────────────────┐
│  Top Navigation Bar (固定顶部)               │
│  Logo | 市场 | 搜索 | 用户                  │
├──────┬──────────────────────────────────────┤
│      │                                       │
│ Side │  Main Content Area                   │
│ Nav  │  (响应式网格布局)                     │
│      │                                       │
│ 固定 │  - 数据卡片                           │
│ 左侧 │  - 图表区域                           │
│      │  - 表格列表                           │
│      │                                       │
└──────┴──────────────────────────────────────┘
```

### 响应式断点

| 断点名称 | 宽度范围 | Side Nav | 布局调整 |
|---------|---------|----------|---------|
| Mobile | 320-767px | 底部导航 | 单列布局，卡片堆叠 |
| Tablet | 768-1023px | 可折叠侧边栏 | 2列网格 |
| Desktop | 1024-1439px | 固定侧边栏 | 3-4列网格 |
| Large Desktop | ≥1440px | 固定侧边栏 | 4-6列网格 |

### 核心设计原则

1. **数据优先**：关键数据一目了然，减少点击层级
2. **视觉层次**：通过字号、字重、颜色区分信息重要性
3. **一致性**：统一的组件、间距、交互模式
4. **可访问性**：高对比度、清晰的状态反馈

---

## 页面设计

### 1. 价值推荐页（首页）

**页面目标**：快速筛选高价值股票，提供清晰推荐理由

#### 布局结构

```
┌─────────────────────────────────────────────┐
│  市场切换 Tabs (A股 | 美股 | 港股)           │
├─────────────────────────────────────────────┤
│  价值筛选器 (可折叠)                        │
│  [ROE] [负债率] [现金流] [市值] [行业]      │
├─────────────────────────────────────────────┤
│  推荐股票列表                               │
│  ┌──────────┬──────────┬──────────┐        │
│  │ 股票卡片 │ 股票卡片 │ 股票卡片 │        │
│  │ - 名称   │ - 名称   │ - 名称   │        │
│  │ - 价格   │ - 价格   │ - 价格   │        │
│  │ - 涨跌   │ - 涨跌   │ - 涨跌   │        │
│  │ - 指标   │ - 指标   │ - 指标   │        │
│  │ - 推荐理由│ - 推荐理由│ - 推荐理由│        │
│  └──────────┴──────────┴──────────┘        │
│  [加载更多]                                 │
└─────────────────────────────────────────────┘
```

#### 核心组件

**1.1 市场切换器 (Market Tabs)**

- **位置**：顶部固定，在导航栏下方
- **样式**：横向 Tab，当前选中高亮
- **交互**：
  - 点击切换市场
  - 切换时显示加载状态
  - 保存上次选择到 localStorage

```jsx
// 组件结构
<MarketTabs>
  <Tab active={market === 'a'} onClick={() => setMarket('a')}>
    A股
  </Tab>
  <Tab active={market === 'us'} onClick={() => setMarket('us')}>
    美股
  </Tab>
  <Tab active={market === 'hk'} onClick={() => setMarket('hk')}>
    港股
  </Tab>
</MarketTabs>
```

**1.2 价值筛选器 (Value Screener)**

- **位置**：市场切换下方，可折叠
- **默认状态**：展开（桌面）/ 收起（移动端）
- **筛选维度**：
  - ROE：滑块范围（0% - 50%+）
  - 负债率：滑块范围（0% - 100%）
  - 现金流：正/负筛选
  - 市值：范围选择
  - 行业：多选下拉

- **交互**：
  - 实时筛选（debounce 300ms）
  - 显示符合条件的股票数量
  - 重置按钮

```jsx
<ValueScreener>
  <SliderFilter
    label="ROE"
    min={0}
    max={50}
    unit="%"
    value={filters.roe}
    onChange={handleRoeChange}
  />
  <SliderFilter
    label="负债率"
    min={0}
    max={100}
    unit="%"
    value={filters.debtRatio}
    onChange={handleDebtChange}
  />
  <ToggleFilter
    label="现金流"
    options={['全部', '正向', '负向']}
    value={filters.cashFlow}
  />
  <SelectFilter
    label="行业"
    options={industries}
    multiple
    value={filters.industries}
  />
  <Button variant="secondary" onClick={resetFilters}>
    重置筛选
  </Button>
</ValueScreener>
```

**1.3 推荐股票卡片 (Stock Recommendation Card)**

- **布局**：响应式网格，3-4列（桌面）/ 1-2列（移动端）
- **信息层次**：
  1. 股票名称 + 代码（最突出）
  2. 当前价格 + 涨跌幅
  3. 关键指标（ROE、负债率、PE）
  4. 推荐理由（折叠，点击展开）

```jsx
<StockCard onClick={() => navigateToDetail(stock.id)}>
  <CardHeader>
    <StockName>{stock.name}</StockName>
    <StockCode>{stock.code}</StockCode>
  </CardHeader>
  
  <PriceSection>
    <CurrentPrice>¥{stock.price}</CurrentPrice>
    <PriceChange positive={stock.change > 0}>
      {stock.change > 0 ? '+' : ''}{stock.change}%
    </PriceChange>
  </PriceSection>
  
  <MetricsGrid>
    <MetricItem>
      <MetricLabel>ROE</MetricLabel>
      <MetricValue positive={stock.roe > 15}>
        {stock.roe}%
      </MetricValue>
    </MetricItem>
    <MetricItem>
      <MetricLabel>负债率</MetricLabel>
      <MetricValue negative={stock.debtRatio > 60}>
        {stock.debtRatio}%
      </MetricValue>
    </MetricItem>
    <MetricItem>
      <MetricLabel>PE</MetricLabel>
      <MetricValue>{stock.pe}</MetricValue>
    </MetricItem>
  </MetricsGrid>
  
  <RecommendationReason>
    <ReasonToggle onClick={toggleReason}>
      {expanded ? '收起' : '查看推荐理由'}
    </ReasonToggle>
    {expanded && <ReasonText>{stock.reason}</ReasonText>}
  </RecommendationReason>
</StockCard>
```

#### 交互细节

- **卡片悬停**：轻微上浮（transform: translateY(-4px)），阴影加深
- **指标颜色编码**：
  - 绿色（#10B981）：正向指标（高ROE、低负债）
  - 红色（#EF4444）：负向指标（低ROE、高负债）
  - 默认色（#94A3B8）：中性
- **加载状态**：骨架屏（Skeleton），模拟卡片布局

---

### 2. 财报分析页

**页面目标**：深度展示单只股票的财务健康状况

#### 布局结构

```
┌─────────────────────────────────────────────┐
│  股票搜索 + 基本信息头部                    │
│  [搜索框] | 股票名称 | 代码 | 当前价        │
├─────────────────────────────────────────────┤
│  财务指标卡片组 (4-6个)                     │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐              │
│  │ROE │ │毛利│ │负债│ │PE  │              │
│  └────┘ └────┘ └────┘ └────┘              │
├─────────────────────────────────────────────┤
│  时间线图表区域                             │
│  [指标选择] [时间范围]                      │
│  ┌─────────────────────────────────────┐   │
│  │  折线图 / 面积图                    │   │
│  │  (5-10年历史数据)                  │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│  财务健康度雷达图                           │
│  ┌───────────┬───────────┐                │
│  │  雷达图   │  评分说明 │                │
│  └───────────┴───────────┘                │
└─────────────────────────────────────────────┘
```

#### 核心组件

**2.1 股票搜索器 (Stock Search)**

- **位置**：页面顶部
- **交互**：
  - 自动补全（输入时显示匹配结果）
  - 支持股票代码、名称、拼音搜索
  - 显示最近搜索历史

```jsx
<StockSearch>
  <SearchInput
    placeholder="搜索股票代码、名称..."
    value={searchQuery}
    onChange={handleSearch}
  />
  {showSuggestions && (
    <SuggestionsDropdown>
      {suggestions.map(stock => (
        <SuggestionItem
          key={stock.id}
          onClick={() => selectStock(stock)}
        >
          <StockSymbol>{stock.code}</StockSymbol>
          <StockName>{stock.name}</StockName>
          <StockMarket>{stock.market}</StockMarket>
        </SuggestionItem>
      ))}
    </SuggestionsDropdown>
  )}
</StockSearch>
```

**2.2 财务指标卡片 (Metric Card)**

- **布局**：横向滚动（移动端）/ 网格（桌面）
- **信息**：
  - 指标名称
  - 当前值
  - 同比变化
  - 趋势图标（上升/下降/持平）

```jsx
<MetricCard>
  <MetricHeader>
    <MetricTitle>ROE（净资产收益率）</MetricTitle>
    <TrendIcon direction={metric.trend} />
  </MetricHeader>
  
  <MetricValue>
    {metric.value}%
  </MetricValue>
  
  <MetricChange positive={metric.change > 0}>
    同比 {metric.change > 0 ? '+' : ''}{metric.change}%
  </MetricChange>
  
  <MetricBenchmark>
    行业平均: {metric.benchmark}%
  </MetricBenchmark>
</MetricCard>
```

**指标卡片组包含**：
1. ROE（净资产收益率）
2. 毛利率
3. 负债率
4. PE（市盈率）
5. 现金流
6. 净利润增长率

**2.3 时间线图表 (Timeline Chart)**

- **图表类型**：折线图（Line Chart）或面积图（Area Chart）
- **时间范围选择**：5年 / 7年 / 10年
- **指标切换**：多选，支持叠加显示
- **交互**：
  - 悬停显示具体数值
  - 双指缩放（移动端）
  - 图例可点击切换显示/隐藏

```jsx
<TimelineChart>
  <ChartControls>
    <MetricSelector
      options={availableMetrics}
      selected={selectedMetrics}
      onChange={setSelectedMetrics}
      multiple
    />
    <TimeRangeSelector
      options={['5年', '7年', '10年']}
      selected={timeRange}
      onChange={setTimeRange}
    />
  </ChartControls>
  
  <ResponsiveContainer width="100%" height={400}>
    <LineChart data={historicalData}>
      <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
      <XAxis dataKey="year" stroke="#94A3B8" />
      <YAxis stroke="#94A3B8" />
      <Tooltip content={<CustomTooltip />} />
      <Legend />
      {selectedMetrics.map(metric => (
        <Line
          key={metric.key}
          type="monotone"
          dataKey={metric.key}
          stroke={metric.color}
          strokeWidth={2}
          dot={{ r: 4 }}
        />
      ))}
    </LineChart>
  </ResponsiveContainer>
</TimelineChart>
```

**2.4 财务健康度雷达图 (Health Radar)**

- **维度**（6个）：
  1. 盈利能力（ROE、净利润率）
  2. 成长性（营收增长率、利润增长率）
  3. 偿债能力（负债率、流动比率）
  4. 运营效率（资产周转率、存货周转率）
  5. 现金流（经营现金流、自由现金流）
  6. 估值（PE、PB 相对行业）

```jsx
<HealthRadar>
  <RadarChart>
    {/* 6维度雷达图 */}
  </RadarChart>
  
  <HealthScore>
    <ScoreValue>85</ScoreValue>
    <ScoreLabel>综合健康度</ScoreLabel>
    <ScoreDescription>
      该公司财务状况优秀，盈利能力强，现金流健康
    </ScoreDescription>
  </HealthScore>
  
  <DimensionBreakdown>
    {dimensions.map(dim => (
      <DimensionItem key={dim.key}>
        <DimensionName>{dim.name}</DimensionName>
        <DimensionScore>{dim.score}/100</DimensionScore>
        <ProgressBar value={dim.score} />
      </DimensionItem>
    ))}
  </DimensionBreakdown>
</HealthRadar>
```

---

### 3. 持股查询页

**页面目标**：可视化展示股东结构和持股变动

#### 布局结构

```
┌─────────────────────────────────────────────┐
│  股票选择 + 基本信息                        │
├─────────────────────────────────────────────┤
│  股东结构饼图 + 十大股东表格                │
│  ┌───────────┬───────────────────────┐     │
│  │  饼图     │  十大股东列表         │     │
│  │  (可交互) │  1. XXX   15%  +2%   │     │
│  │           │  2. YYY   12%  -1%   │     │
│  │           │  ...                 │     │
│  └───────────┴───────────────────────┘     │
├─────────────────────────────────────────────┤
│  机构持仓列表                               │
│  [筛选] [排序]                              │
│  ┌─────────────────────────────────────┐   │
│  │ 机构名称 | 持股数 | 占比 | 变动     │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│  持股变动时间线                             │
│  ┌─────────────────────────────────────┐   │
│  │  时间线图表（增持/减持事件）        │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

#### 核心组件

**3.1 股东结构饼图 (Shareholder Pie Chart)**

- **图表类型**：环形图（Donut Chart）
- **分类**：
  - 机构投资者
  - 个人投资者
  - 内部人持股
  - 其他

```jsx
<ShareholderPieChart>
  <ResponsiveContainer width="100%" height={300}>
    <PieChart>
      <Pie
        data={shareholderData}
        cx="50%"
        cy="50%"
        innerRadius={60}
        outerRadius={100}
        paddingAngle={5}
        dataKey="percentage"
      >
        {shareholderData.map((entry, index) => (
          <Cell key={index} fill={entry.color} />
        ))}
      </Pie>
      <Tooltip content={<CustomTooltip />} />
      <Legend />
    </PieChart>
  </ResponsiveContainer>
  
  <ChartCenter>
    <TotalShares>总股本</TotalShares>
    <SharesValue>{totalShares}</SharesValue>
  </ChartCenter>
</ShareholderPieChart>
```

**3.2 十大股东表格 (Top Shareholders Table)**

- **列信息**：
  1. 排名
  2. 股东名称
  3. 持股数
  4. 持股比例
  5. 较上期变动
  6. 股东性质（机构/个人/内部人）

```jsx
<TopShareholdersTable>
  <TableHeader>
    <TableRow>
      <TableCell>排名</TableCell>
      <TableCell>股东名称</TableCell>
      <TableCell>持股数</TableCell>
      <TableCell>持股比例</TableCell>
      <TableCell>变动</TableCell>
      <TableCell>性质</TableCell>
    </TableRow>
  </TableHeader>
  
  <TableBody>
    {topShareholders.map((shareholder, index) => (
      <TableRow key={shareholder.id}>
        <TableCell>{index + 1}</TableCell>
        <TableCell>{shareholder.name}</TableCell>
        <TableCell>{formatNumber(shareholder.shares)}</TableCell>
        <TableCell>{shareholder.percentage}%</TableCell>
        <TableCell>
          <ChangeIndicator positive={shareholder.change > 0}>
            {shareholder.change > 0 ? '+' : ''}{shareholder.change}%
          </ChangeIndicator>
        </TableCell>
        <TableCell>
          <Badge variant={shareholder.type}>
            {shareholder.typeLabel}
          </Badge>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</TopShareholdersTable>
```

**3.3 机构持仓列表 (Institutional Holdings)**

- **筛选维度**：
  - 机构类型（基金/券商/保险/外资等）
  - 持股变动（增持/减持/不变）
- **排序选项**：
  - 持股数量（降序）
  - 持股比例（降序）
  - 变动幅度（降序）

```jsx
<InstitutionalHoldings>
  <FilterBar>
    <SelectFilter
      label="机构类型"
      options={institutionTypes}
      value={filterType}
      onChange={setFilterType}
    />
    <SelectFilter
      label="持股变动"
      options={['全部', '增持', '减持', '不变']}
      value={filterChange}
      onChange={setFilterChange}
    />
  </FilterBar>
  
  <HoldingsList>
    {institutionalHoldings.map(holding => (
      <HoldingCard key={holding.id}>
        <InstitutionInfo>
          <InstitutionName>{holding.name}</InstitutionName>
          <InstitutionType>{holding.type}</InstitutionType>
        </InstitutionInfo>
        
        <HoldingMetrics>
          <Metric>
            <Label>持股数</Label>
            <Value>{formatNumber(holding.shares)}</Value>
          </Metric>
          <Metric>
            <Label>占比</Label>
            <Value>{holding.percentage}%</Value>
          </Metric>
          <Metric>
            <Label>变动</Label>
            <Value positive={holding.change > 0}>
              {holding.change > 0 ? '+' : ''}{holding.change}%
            </Value>
          </Metric>
        </HoldingMetrics>
      </HoldingCard>
    ))}
  </HoldingsList>
</InstitutionalHoldings>
```

**3.4 持股变动时间线 (Holdings Timeline)**

- **图表类型**：时间线图（Timeline Chart）
- **事件类型**：
  - 大股东增持（绿色）
  - 大股东减持（红色）
  - 机构调研（蓝色）
  - 限售解禁（橙色）

```jsx
<HoldingsTimeline>
  <TimelineChart>
    {/* 时间线可视化 */}
    <TimelineAxis>
      {events.map(event => (
        <TimelineEvent
          key={event.id}
          type={event.type}
          position={calculatePosition(event.date)}
        >
          <EventMarker type={event.type} />
          <EventTooltip>
            <EventDate>{formatDate(event.date)}</EventDate>
            <EventDescription>{event.description}</EventDescription>
            <EventDetails>{event.details}</EventDetails>
          </EventTooltip>
        </TimelineEvent>
      ))}
    </TimelineAxis>
  </TimelineChart>
  
  <EventLegend>
    <LegendItem type="increase">增持</LegendItem>
    <LegendItem type="decrease">减持</LegendItem>
    <LegendItem type="research">调研</LegendItem>
    <LegendItem type="unlock">解禁</LegendItem>
  </EventLegend>
</HoldingsTimeline>
```

---

## 配色方案

### 主题色板（Dark Mode）

基于 **金融产品专业风格**，采用深色主题：

| 色彩角色 | 色值 | 用途 | 示例 |
|---------|------|------|------|
| **主背景** | `#0A0E27` | 页面背景 | 整体背景 |
| **次背景** | `#1E293B` | 卡片背景 | 数据卡片、表格 |
| **三背景** | `#334155` | 悬浮层、模态框 | Dropdown、Modal |
| **主色** | `#2563EB` | 品牌色、主要操作 | 按钮、链接、图标 |
| **次色** | `#3B82F6` | 辅助色 | 次要按钮、图标 |
| **强调色** | `#F97316` | CTA、重要提示 | 主要CTA按钮 |
| **正向色** | `#10B981` | 增长、正向指标 | 涨幅、正向变化 |
| **负向色** | `#EF4444` | 下降、负向指标 | 跌幅、负向变化 |
| **警告色** | `#F59E0B` | 警告、注意 | 提示信息 |
| **主文字** | `#F8FAFC` | 主要文本 | 标题、正文 |
| **次文字** | `#94A3B8` | 次要文本 | 说明、标签 |
| **禁用文字** | `#64748B` | 禁用状态 | Disabled文本 |
| **边框** | `#334155` | 分割线、边框 | 卡片边框、分割线 |

### 语义化色彩变量

```css
:root {
  /* 背景色 */
  --bg-primary: #0A0E27;
  --bg-secondary: #1E293B;
  --bg-tertiary: #334155;
  
  /* 品牌色 */
  --color-primary: #2563EB;
  --color-secondary: #3B82F6;
  --color-accent: #F97316;
  
  /* 状态色 */
  --color-positive: #10B981;
  --color-negative: #EF4444;
  --color-warning: #F59E0B;
  
  /* 文字色 */
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-disabled: #64748B;
  
  /* 边框色 */
  --border-color: #334155;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.6);
}
```

### 数据可视化配色

为图表提供清晰的色彩区分：

```css
:root {
  /* 图表配色方案（6色） */
  --chart-color-1: #2563EB; /* 主色蓝 */
  --chart-color-2: #10B981; /* 正向绿 */
  --chart-color-3: #F97316; /* 强调橙 */
  --chart-color-4: #8B5CF6; /* 紫色 */
  --chart-color-5: #EC4899; /* 粉色 */
  --chart-color-6: #14B8A6; /* 青色 */
  
  /* 图表网格线 */
  --chart-grid: #1E293B;
  --chart-axis: #94A3B8;
}
```

### 浅色主题（Light Mode）备选

```css
[data-theme="light"] {
  --bg-primary: #F8FAFC;
  --bg-secondary: #FFFFFF;
  --bg-tertiary: #F1F5F9;
  
  --text-primary: #1E293B;
  --text-secondary: #64748B;
  --text-disabled: #94A3B8;
  
  --border-color: #E2E8F0;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

---

## 组件规范

### 1. 按钮 (Button)

#### 尺寸规范

| 尺寸 | 高度 | 内边距 | 字号 | 使用场景 |
|------|------|--------|------|---------|
| Small | 32px | 8px 12px | 14px | 表格操作、次要操作 |
| Medium | 40px | 12px 16px | 16px | 主要操作、表单提交 |
| Large | 48px | 16px 24px | 18px | 页面主CTA |

#### 变体

```jsx
// Primary Button - 主要操作
<Button variant="primary" size="medium">
  查看详情
</Button>

// Secondary Button - 次要操作
<Button variant="secondary" size="medium">
  取消
</Button>

// Ghost Button - 轻量操作
<Button variant="ghost" size="small">
  编辑
</Button>

// Danger Button - 危险操作
<Button variant="danger" size="medium">
  删除
</Button>
```

#### 样式

```css
/* Primary Button */
.btn-primary {
  background: var(--color-accent);
  color: var(--text-primary);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #EA580C;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.btn-secondary:hover {
  background: rgba(37, 99, 235, 0.1);
}
```

### 2. 卡片 (Card)

#### 基础卡片

```css
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}
```

#### 数据卡片（带指标）

```jsx
<DataCard>
  <CardHeader>
    <CardTitle>ROE</CardTitle>
    <CardSubtitle>净资产收益率</CardSubtitle>
  </CardHeader>
  
  <CardValue>
    <Value>18.5%</Value>
    <Trend positive>↑ 2.3%</Trend>
  </CardValue>
  
  <CardFooter>
    <Benchmark>行业平均: 12%</Benchmark>
  </CardFooter>
</DataCard>
```

```css
.data-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.data-card .value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.data-card .trend {
  font-size: 14px;
  font-weight: 600;
}

.data-card .trend.positive {
  color: var(--color-positive);
}

.data-card .trend.negative {
  color: var(--color-negative);
}
```

### 3. 表格 (Table)

#### 基础表格

```jsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHeaderCell>股东名称</TableHeaderCell>
      <TableHeaderCell>持股数</TableHeaderCell>
      <TableHeaderCell>持股比例</TableHeaderCell>
      <TableHeaderCell>变动</TableHeaderCell>
    </TableRow>
  </TableHeader>
  
  <TableBody>
    {data.map(row => (
      <TableRow key={row.id}>
        <TableCell>{row.name}</TableCell>
        <TableCell>{row.shares}</TableCell>
        <TableCell>{row.percentage}%</TableCell>
        <TableCell>
          <ChangeIndicator positive={row.change > 0}>
            {row.change > 0 ? '+' : ''}{row.change}%
          </ChangeIndicator>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

#### 样式

```css
.table {
  width: 100%;
  border-collapse: collapse;
}

.table-header-cell {
  text-align: left;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--border-color);
}

.table-row {
  transition: background 0.2s ease;
}

.table-row:hover {
  background: rgba(37, 99, 235, 0.05);
}

.table-cell {
  padding: 16px;
  font-size: 15px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}
```

### 4. 图表 (Charts)

#### 图表容器

```css
.chart-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  height: 400px;
}
```

#### 图表控件

```jsx
<ChartControls>
  <MetricSelector>
    <Select value={selectedMetric} onChange={handleMetricChange}>
      <Option value="roe">ROE</Option>
      <Option value="revenue">营收</Option>
      <Option value="profit">净利润</Option>
    </Select>
  </MetricSelector>
  
  <TimeRangeSelector>
    <ButtonGroup>
      <Button active={range === '5y'}>5年</Button>
      <Button active={range === '7y'}>7年</Button>
      <Button active={range === '10y'}>10年</Button>
    </ButtonGroup>
  </TimeRangeSelector>
</ChartControls>
```

#### Tooltip 样式

```css
.chart-tooltip {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: var(--shadow-lg);
}

.tooltip-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.tooltip-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
```

### 5. 输入框 (Input)

```jsx
<Input
  type="text"
  placeholder="搜索股票..."
  value={searchQuery}
  onChange={handleSearch}
  leftIcon={<SearchIcon />}
/>
```

```css
.input {
  width: 100%;
  height: 48px;
  padding: 0 16px 0 44px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 16px;
  transition: all 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input::placeholder {
  color: var(--text-disabled);
}
```

### 6. 徽章 (Badge)

```jsx
<Badge variant="success">增持</Badge>
<Badge variant="danger">减持</Badge>
<Badge variant="info">机构</Badge>
```

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 9999px;
}

.badge.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-positive);
}

.badge.danger {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-negative);
}

.badge.info {
  background: rgba(37, 99, 235, 0.1);
  color: var(--color-primary);
}
```

### 7. 导航 (Navigation)

#### 顶部导航栏

```jsx
<TopNavbar>
  <NavbarLeft>
    <Logo />
    <MarketTabs />
  </NavbarLeft>
  
  <NavbarCenter>
    <SearchInput />
  </NavbarCenter>
  
  <NavbarRight>
    <ThemeToggle />
    <UserMenu />
  </NavbarRight>
</TopNavbar>
```

```css
.top-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
}
```

#### 侧边导航

```jsx
<SideNav>
  <NavItem active>
    <NavIcon><HomeIcon /></NavIcon>
    <NavLabel>价值推荐</NavLabel>
  </NavItem>
  
  <NavItem>
    <NavIcon><ChartIcon /></NavIcon>
    <NavLabel>财报分析</NavLabel>
  </NavItem>
  
  <NavItem>
    <NavIcon><UsersIcon /></NavIcon>
    <NavLabel>持股查询</NavLabel>
  </NavItem>
</SideNav>
```

```css
.side-nav {
  position: fixed;
  left: 0;
  top: 64px;
  bottom: 0;
  width: 240px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  padding: 24px 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(37, 99, 235, 0.05);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(37, 99, 235, 0.1);
  color: var(--color-primary);
}
```

---

## 交互规范

### 动画时长

| 交互类型 | 时长 | 缓动函数 |
|---------|------|---------|
| 按钮悬停 | 150ms | ease-out |
| 卡片悬停 | 300ms | ease-out |
| 页面切换 | 300ms | ease-in-out |
| 模态框弹出 | 200ms | ease-out |
| 图表加载 | 500ms | ease-in-out |
| Toast 提示 | 300ms | ease-out |

### 加载状态

#### 骨架屏 (Skeleton)

```jsx
<SkeletonCard>
  <Skeleton width="60%" height="24px" />
  <Skeleton width="40%" height="16px" />
  <Skeleton width="100%" height="80px" />
</SkeletonCard>
```

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-secondary) 25%,
    var(--bg-tertiary) 50%,
    var(--bg-secondary) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```

### 空状态

```jsx
<EmptyState>
  <EmptyIcon />
  <EmptyTitle>暂无数据</EmptyTitle>
  <EmptyDescription>
    当前筛选条件下没有找到符合条件的股票
  </EmptyDescription>
  <Button variant="primary" onClick={resetFilters}>
    重置筛选
  </Button>
</EmptyState>
```

---

## 响应式设计

### 移动端适配

#### 布局调整

- **导航**：侧边导航 → 底部导航
- **卡片**：3-4列 → 1列
- **表格**：横向滚动或卡片式展示
- **图表**：全宽，高度自适应

#### 触控优化

- **最小触控尺寸**：44px × 44px
- **按钮间距**：8px 以上
- **滚动区域**：避免嵌套滚动

```css
/* 移动端断点 */
@media (max-width: 767px) {
  .side-nav {
    display: none;
  }
  
  .bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 64px;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: space-around;
    align-items: center;
  }
  
  .stock-card-grid {
    grid-template-columns: 1fr;
  }
  
  .table-responsive {
    overflow-x: auto;
  }
}
```

---

## 可访问性

### 对比度要求

- **正文文字**：≥ 4.5:1（WCAG AA）
- **大标题**：≥ 3:1
- **图标**：≥ 3:1

### 键盘导航

- 所有交互元素可通过 Tab 键访问
- 使用 Enter/Space 激活按钮
- 使用 Esc 关闭模态框

### 屏幕阅读器

```jsx
<button aria-label="搜索股票">
  <SearchIcon aria-hidden="true" />
</button>

<img src="chart.png" alt="ROE 趋势图：近5年从12%增长至18%" />
```

### 减少动画

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 技术栈建议

### 推荐技术栈

- **框架**：React 18+ / Next.js 14+
- **样式**：Tailwind CSS + CSS Modules
- **图表库**：Recharts / Chart.js / ECharts
- **状态管理**：Zustand / Jotai
- **图标**：Lucide React / Heroicons
- **动画**：Framer Motion

### 组件库参考

- **shadcn/ui**：高质量、可定制的 React 组件
- **Radix UI**：无样式的可访问组件原语
- **Headless UI**：无样式的 UI 组件

---

## 设计交付清单

### 设计文件

- [ ] Figma 设计稿（完整页面）
- [ ] 组件库（Figma Components）
- [ ] 设计系统文档（Design Tokens）
- [ ] 交互原型（可点击原型）

### 开发资源

- [ ] 设计 Token（JSON/CSS 变量）
- [ ] 图标资源（SVG）
- [ ] 字体文件（WOFF2）
- [ ] 图片资源（WebP/AVIF）

### 文档

- [ ] 组件使用指南
- [ ] 交互规范文档
- [ ] 可访问性检查清单
- [ ] 响应式断点说明

---

## 总结

ValueGraph 前端 UI 设计遵循以下核心原则：

1. **专业简洁**：深色主题 + 清晰的数据可视化
2. **数据驱动**：关键指标一目了然，减少点击层级
3. **一致性**：统一的设计系统、组件规范
4. **可访问性**：高对比度、清晰的交互反馈
5. **响应式**：桌面/平板/移动端全适配

通过本设计规范，开发团队可以快速构建高质量、专业的价值投资平台前端界面。

---

**设计者**: Designer Agent  
**版本**: v1.0  
**日期**: 2026-03-24  
**项目**: ValueGraph 价值投资知识图谱平台
