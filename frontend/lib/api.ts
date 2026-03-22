import axios from 'axios'

// 直接连接后端 API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

// API 客户端
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export interface Stock {
  code: string
  name: string
  price: number
  change: number
  changePercent: number
  market: string
}

export interface FinancialData {
  date: string
  revenue: number
  netIncome: number
  eps: number
  roe: number
}

export interface Shareholder {
  name: string
  shares: number
  percentage: number
  change: number
}

// 获取推荐股票列表
export async function fetchStocks(market: 'a-share' | 'us-market'): Promise<Stock[]> {
  try {
    const response = await apiClient.get(`/api/stocks/recommend`, {
      params: {
        market,
        top_n: 10
      }
    })
    
    // 后端返回格式: { success: true, data: [...] }
    if (response.data.success && response.data.data) {
      return response.data.data.map((stock: any) => ({
        code: stock.code || stock.stock_code,
        name: stock.name || stock.stock_name,
        price: stock.price || 0,
        change: stock.change || 0,
        changePercent: stock.change_percent || stock.changePercent || 0,
        market: market
      }))
    }
    
    return []
  } catch (error) {
    console.error('获取股票数据失败:', error)
    throw error
  }
}

// 获取股票详情
export async function fetchStockDetail(code: string) {
  try {
    const response = await apiClient.get(`/api/stocks/${code}`)
    return response.data
  } catch (error) {
    console.error('获取股票详情失败:', error)
    throw error
  }
}

// 获取财报数据
export async function fetchFinancialData(code: string): Promise<FinancialData[]> {
  try {
    const response = await apiClient.get(`/api/stocks/${code}`)
    
    // 后端返回格式: { financial_data: [...] }
    if (response.data.financial_data) {
      return response.data.financial_data.map((item: any) => ({
        date: item.date || item.report_date,
        revenue: item.revenue || 0,
        netIncome: item.net_income || item.netIncome || 0,
        eps: item.eps || 0,
        roe: item.roe || 0
      }))
    }
    
    return []
  } catch (error) {
    console.error('获取财报数据失败:', error)
    throw error
  }
}

// 获取股东信息
export async function fetchShareholders(code: string): Promise<Shareholder[]> {
  try {
    const response = await apiClient.get(`/api/stocks/${code}`)
    
    // 后端返回格式: { shareholders: [...] }
    if (response.data.shareholders) {
      return response.data.shareholders.map((item: any) => ({
        name: item.name || item.shareholder_name,
        shares: item.shares || item.share_number || 0,
        percentage: item.percentage || item.share_ratio || 0,
        change: item.change || item.change_ratio || 0
      }))
    }
    
    return []
  } catch (error) {
    console.error('获取股东数据失败:', error)
    throw error
  }
}
