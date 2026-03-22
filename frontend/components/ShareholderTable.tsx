'use client'
import { Table, Card, Skeleton, message, Tag } from 'antd'
import { RiseOutlined, FallOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { fetchShareholders, Shareholder } from '@/lib/api'

interface ShareholderTableProps {
  code: string
}

export default function ShareholderTable({ code }: ShareholderTableProps) {
  const [data, setData] = useState<Shareholder[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [code])

  const loadData = async () => {
    try {
      setLoading(true)
      const shareholders = await fetchShareholders(code)
      setData(shareholders)
    } catch (error) {
      message.warning('使用模拟数据展示')
      // 模拟数据
      setData([
        { name: '香港中央结算有限公司', shares: 1250000000, percentage: 9.98, change: 0.5 },
        { name: '中国证券金融股份有限公司', shares: 890000000, percentage: 7.09, change: -0.2 },
        { name: '中央汇金投资有限责任公司', shares: 680000000, percentage: 5.42, change: 0 },
        { name: '全国社保基金一一五组合', shares: 450000000, percentage: 3.59, change: 0.3 },
        { name: '中国人寿保险股份有限公司', shares: 320000000, percentage: 2.55, change: -0.1 },
      ])
    } finally {
      setLoading(false)
    }
  }

  const columns: ColumnsType<Shareholder> = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => index + 1,
    },
    {
      title: '股东名称',
      dataIndex: 'name',
      key: 'name',
      width: 300,
    },
    {
      title: '持股数量',
      dataIndex: 'shares',
      key: 'shares',
      width: 150,
      render: (shares: number) => `${(shares / 100000000).toFixed(2)}亿股`,
      sorter: (a, b) => a.shares - b.shares,
    },
    {
      title: '持股比例',
      dataIndex: 'percentage',
      key: 'percentage',
      width: 120,
      render: (percentage: number) => `${percentage.toFixed(2)}%`,
      sorter: (a, b) => a.percentage - b.percentage,
    },
    {
      title: '较上期变化',
      dataIndex: 'change',
      key: 'change',
      width: 120,
      render: (change: number) => {
        if (change === 0) return <Tag>不变</Tag>
        const color = change > 0 ? 'red' : 'green'
        const icon = change > 0 ? <RiseOutlined /> : <FallOutlined />
        return (
          <Tag color={color} icon={icon}>
            {change > 0 ? '+' : ''}{change.toFixed(2)}%
          </Tag>
        )
      },
      sorter: (a, b) => a.change - b.change,
    },
  ]

  if (loading) {
    return <Skeleton active />
  }

  return (
    <Card>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="name"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />
    </Card>
  )
}
