'use client'
import { Tabs } from 'antd'
import { ReactNode } from 'react'

interface MarketTabsProps {
  onMarketChange?: (market: 'a-share' | 'us-market') => void
  children?: Record<string, ReactNode>
}

export default function MarketTabs({ onMarketChange, children }: MarketTabsProps) {
  const items = [
    {
      key: 'a-share',
      label: '🇨🇳 A股市场',
      children: children?.['a-share'],
    },
    {
      key: 'us-market',
      label: '🇺🇸 美股市场',
      children: children?.['us-market'],
    },
  ]

  return (
    <Tabs
      defaultActiveKey="a-share"
      items={items}
      onChange={(key) => onMarketChange?.(key as 'a-share' | 'us-market')}
    />
  )
}
