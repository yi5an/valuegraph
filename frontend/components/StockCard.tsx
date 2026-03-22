'use client'
import { Card, List, Tag, Skeleton, message } from 'antd'
import { RiseOutlined, FallOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { fetchStocks } from '@/lib/api'

interface Stock {
  code: string
  name: string
  price: number
  change: number
  changePercent: number
  market: string
}

interface StockCardProps {
  market: 'a-share' | 'us-market'
}

export default function StockCard({ market }: StockCardProps) {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStocks()
  }, [market])

  const loadStocks = async () => {
    try {
      setLoading(true)
      const data = await fetchStocks(market)
      setStocks(data)
    } catch (error) {
      message.error('加载股票数据失败')
      // 使用模拟数据
      setStocks(getMockData(market))
    } finally {
      setLoading(false)
    }
  }

  const getMockData = (market: string): Stock[] => {
    if (market === 'a-share') {
      return [
        { code: '600519', name: '贵州茅台', price: 1688.00, change: 28.50, changePercent: 1.72, market: 'a-share' },
        { code: '000858', name: '五粮液', price: 168.50, change: -2.30, changePercent: -1.35, market: 'a-share' },
        { code: '601318', name: '中国平安', price: 48.20, change: 0.85, changePercent: 1.79, market: 'a-share' },
      ]
    }
    return [
      { code: 'AAPL', name: '苹果公司', price: 178.50, change: 2.35, changePercent: 1.33, market: 'us-market' },
      { code: 'MSFT', name: '微软', price: 378.90, change: -1.20, changePercent: -0.32, market: 'us-market' },
      { code: 'GOOGL', name: '谷歌', price: 141.80, change: 3.45, changePercent: 2.49, market: 'us-market' },
    ]
  }

  if (loading) {
    return <Skeleton active />
  }

  return (
    <List
      grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4 }}
      dataSource={stocks}
      renderItem={(stock) => (
        <List.Item>
          <Link href={`/stocks/${stock.code}`}>
            <Card 
              hoverable
              className="cursor-pointer"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-lg font-semibold">{stock.name}</div>
                  <div className="text-gray-500 text-sm">{stock.code}</div>
                </div>
                <Tag color={stock.change >= 0 ? 'red' : 'green'}>
                  {stock.market === 'a-share' ? 'A股' : '美股'}
                </Tag>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold">¥{stock.price.toFixed(2)}</div>
                <div className={`flex items-center gap-1 mt-1 ${stock.change >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {stock.change >= 0 ? <RiseOutlined /> : <FallOutlined />}
                  <span>{stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}</span>
                  <span>({stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)</span>
                </div>
              </div>
            </Card>
          </Link>
        </List.Item>
      )}
    />
  )
}
