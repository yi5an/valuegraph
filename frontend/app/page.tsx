'use client'
import { Tabs, Card } from 'antd'
import StockCard from '@/components/StockCard'

export default function Home() {
  return (
    <div className="container mx-auto p-6">
      <Card className="mb-6">
        <h1 className="text-3xl font-bold text-center">
          ValueGraph - 价值投资知识图谱
        </h1>
        <p className="text-center text-gray-600 mt-2">
          多市场价值投资推荐 · 财报深度分析 · 持股信息查询
        </p>
      </Card>

      <Tabs
        defaultActiveKey="a-share"
        items={[
          { 
            key: 'a-share', 
            label: '🇨🇳 A股市场', 
            children: <StockCard market="a-share" /> 
          },
          { 
            key: 'us-market', 
            label: '🇺🇸 美股市场', 
            children: <StockCard market="us-market" /> 
          }
        ]}
      />
    </div>
  )
}
