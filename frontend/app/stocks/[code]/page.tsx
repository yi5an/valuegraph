'use client'
import { Card, Tabs, Skeleton, message, Typography } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { use } from 'react'
import FinancialChart from '@/components/FinancialChart'
import ShareholderTable from '@/components/ShareholderTable'

const { Title } = Typography

export default function StockDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params)

  return (
    <div className="container mx-auto p-6">
      <Link href="/" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4">
        <ArrowLeftOutlined />
        返回首页
      </Link>

      <Card className="mb-6">
        <Title level={2}>股票详情 - {code}</Title>
        <p className="text-gray-600">财报分析与持股信息</p>
      </Card>

      <Tabs
        defaultActiveKey="financials"
        items={[
          {
            key: 'financials',
            label: '📊 财报分析',
            children: <FinancialChart code={code} />,
          },
          {
            key: 'shareholders',
            label: '👥 持股信息',
            children: <ShareholderTable code={code} />,
          },
        ]}
      />
    </div>
  )
}
