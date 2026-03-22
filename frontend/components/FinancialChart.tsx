'use client'
import { Card, Skeleton, message } from 'antd'
import ReactECharts from 'echarts-for-react'
import { useEffect, useState } from 'react'
import { fetchFinancialData, FinancialData } from '@/lib/api'

interface FinancialChartProps {
  code: string
}

export default function FinancialChart({ code }: FinancialChartProps) {
  const [data, setData] = useState<FinancialData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [code])

  const loadData = async () => {
    try {
      setLoading(true)
      const financialData = await fetchFinancialData(code)
      setData(financialData)
    } catch (error) {
      message.warning('使用模拟数据展示')
      // 模拟数据
      setData([
        { date: '2023-Q1', revenue: 1000, netIncome: 150, eps: 1.5, roe: 12.5 },
        { date: '2023-Q2', revenue: 1200, netIncome: 180, eps: 1.8, roe: 13.2 },
        { date: '2023-Q3', revenue: 1150, netIncome: 170, eps: 1.7, roe: 12.8 },
        { date: '2023-Q4', revenue: 1400, netIncome: 210, eps: 2.1, roe: 14.5 },
        { date: '2024-Q1', revenue: 1500, netIncome: 230, eps: 2.3, roe: 15.2 },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Skeleton active />
  }

  const option = {
    title: {
      text: '财务指标趋势',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['营业收入', '净利润', '每股收益', 'ROE'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date),
    },
    yAxis: [
      {
        type: 'value',
        name: '金额/元',
        position: 'left',
      },
      {
        type: 'value',
        name: '百分比/%',
        position: 'right',
      },
    ],
    series: [
      {
        name: '营业收入',
        type: 'line',
        data: data.map(d => d.revenue),
        smooth: true,
      },
      {
        name: '净利润',
        type: 'line',
        data: data.map(d => d.netIncome),
        smooth: true,
      },
      {
        name: '每股收益',
        type: 'bar',
        data: data.map(d => d.eps),
      },
      {
        name: 'ROE',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(d => d.roe),
        smooth: true,
      },
    ],
  }

  return (
    <Card>
      <ReactECharts option={option} style={{ height: '400px' }} />
    </Card>
  )
}
