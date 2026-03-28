import { mockData } from "@/lib/mockData";
import {
  FinancialRecord,
  ShareholderRecord,
  Stock,
  StockFilters
} from "@/lib/types";

/**
 * API 响应包装格式（后端统一格式）
 */
interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: Record<string, unknown>;
}

/**
 * 后端股票推荐 schema（字段名与前端不同）
 */
interface BackendStockRecommend {
  stock_code: string;
  name: string;
  market: string;
  industry?: string;
  sector?: string;
  market_cap?: number;
  latest_roe?: number;
  latest_pe?: number;
  debt_ratio?: number;
  recommendation_score?: number;
  recommendation_reason?: string;
}

/**
 * 后端财报详情 schema
 */
interface BackendFinancialDetail {
  stock_code: string;
  name: string;
  timeline: Array<{
    report_date: string;
    report_type: string;
    revenue?: number;
    revenue_yoy?: number;
    net_profit?: number;
    net_profit_yoy?: number;
    roe?: number;
    gross_margin?: number;
    debt_ratio?: number;
    operating_cash_flow?: number;
    eps?: number;
    bvps?: number;
  }>;
  chart_data?: {
    dates: string[];
    revenues: number[];
    net_profits: number[];
    roes: number[];
  };
  health_score?: {
    overall: number;
    profitability: number;
    solvency: number;
    growth: number;
    operation: number;
  };
}

/**
 * 后端股东详情 schema
 */
interface BackendShareholderDetail {
  stock_code: string;
  name: string;
  report_date: string;
  top_10_shareholders: Array<{
    rank: number;
    holder_name: string;
    hold_amount?: number;
    hold_ratio?: number;
    holder_type?: string;
    change?: string;
  }>;
  institutional_holders: Array<{
    institution_name: string;
    hold_amount?: number;
    hold_ratio?: number;
    institution_type?: string;
    change_ratio?: number;
  }>;
  holder_distribution?: {
    institutional: number;
    individual: number;
    foreign: number;
  };
}

/**
 * 映射市场代码到前端显示名称
 */
function mapMarketCode(code: string): "A股" | "美股" | "港股" {
  const marketMap: Record<string, "A股" | "美股" | "港股"> = {
    A: "A股",
    US: "美股",
    HK: "港股"
  };
  return marketMap[code] || "A股";
}

/**
 * 转换后端股票数据到前端格式
 */
function mapStockFromBackend(backend: BackendStockRecommend): Stock {
  return {
    code: backend.stock_code,
    name: backend.name,
    market: mapMarketCode(backend.market),
    price: 0, // 后端未返回实时价格
    changePercent: 0, // 后端未返回涨跌幅
    roe: backend.latest_roe || 0,
    debtRatio: backend.debt_ratio || 0,
    pe: backend.latest_pe || 0,
    reason: backend.recommendation_reason || "",
    tags: backend.industry ? [backend.industry] : []
  };
}

/**
 * 转换后端财报数据到前端格式
 */
function mapFinancialFromBackend(backend: BackendFinancialDetail): FinancialRecord {
  const metrics: FinancialRecord["metrics"] = [];
  
  // 从最新的 timeline 数据提取指标
  const latest = backend.timeline[0];
  if (latest) {
    if (latest.roe !== undefined) {
      metrics.push({ label: "ROE", value: `${latest.roe.toFixed(1)}%`, tone: latest.roe >= 15 ? "positive" : "negative" });
    }
    if (latest.gross_margin !== undefined) {
      metrics.push({ label: "毛利率", value: `${latest.gross_margin.toFixed(1)}%`, tone: "positive" });
    }
    if (latest.debt_ratio !== undefined) {
      metrics.push({ label: "负债率", value: `${latest.debt_ratio.toFixed(1)}%`, tone: latest.debt_ratio <= 50 ? "positive" : "negative" });
    }
    if (latest.net_profit_yoy !== undefined) {
      metrics.push({ label: "净利润增长率", value: `${latest.net_profit_yoy.toFixed(1)}%`, tone: latest.net_profit_yoy >= 0 ? "positive" : "negative" });
    }
  }
  
  // 转换历史数据
  const history: FinancialRecord["history"] = backend.timeline.map((item) => ({
    year: item.report_date.substring(0, 4),
    revenue: item.revenue || 0,
    netProfit: item.net_profit || 0,
    roe: item.roe || 0,
    grossMargin: item.gross_margin || 0,
    cashFlow: item.operating_cash_flow || 0
  })).reverse();
  
  // 转换健康度数据
  const health: FinancialRecord["health"] = backend.health_score ? [
    { subject: "盈利", score: backend.health_score.profitability, fullMark: 100 },
    { subject: "成长", score: backend.health_score.growth, fullMark: 100 },
    { subject: "偿债", score: backend.health_score.solvency, fullMark: 100 },
    { subject: "运营", score: backend.health_score.operation, fullMark: 100 }
  ] : [];
  
  return {
    code: backend.stock_code,
    company: backend.name,
    metrics,
    history,
    health
  };
}

/**
 * 转换后端股东数据到前端格式
 */
function mapShareholderFromBackend(backend: BackendShareholderDetail): ShareholderRecord {
  // 转换持股分布
  const ownership: ShareholderRecord["ownership"] = backend.holder_distribution ? [
    { name: "机构投资者", value: backend.holder_distribution.institutional },
    { name: "个人投资者", value: backend.holder_distribution.individual },
    { name: "外资", value: backend.holder_distribution.foreign }
  ] : [];
  
  // 转换十大股东
  const topHolders: ShareholderRecord["topHolders"] = backend.top_10_shareholders.map((holder) => ({
    rank: holder.rank,
    name: holder.holder_name,
    shares: holder.hold_amount ? `${(holder.hold_amount / 100000000).toFixed(2)}亿` : "-",
    ratio: holder.hold_ratio ? `${holder.hold_ratio.toFixed(2)}%` : "-",
    change: holder.change || "未变"
  }));
  
  // 转换机构持仓
  const institutions: ShareholderRecord["institutions"] = backend.institutional_holders.map((inst) => ({
    institution: inst.institution_name,
    position: inst.hold_amount ? `${(inst.hold_amount / 100000000).toFixed(2)}亿` : "-",
    ratio: inst.hold_ratio ? `${inst.hold_ratio.toFixed(2)}%` : "-",
    action: inst.change_ratio !== undefined ? (inst.change_ratio > 0 ? "增持" : inst.change_ratio < 0 ? "减持" : "持平") : "持平"
  }));
  
  return {
    code: backend.stock_code,
    company: backend.name,
    ownership,
    topHolders,
    institutions
  };
}

/**
 * Fetch stock recommendations with fallback to mock data.
 */
export async function getStocks(
  market: string,
  filters: StockFilters
): Promise<Stock[]> {
  try {
    // 映射前端市场名称到后端代码
    const marketMap: Record<string, string> = {
      "A股": "A",
      "美股": "US",
      "港股": "HK"
    };
    
    const params = new URLSearchParams({
      market: marketMap[market] || "A",
      min_roe: String(filters.roeMin),
      max_debt_ratio: String(filters.debtMax)
    });
    
    const res = await fetch(`/api/stocks?${params.toString()}`, {
      next: { revalidate: 60 }
    });
    
    if (!res.ok) {
      throw new Error("Failed to fetch stock list");
    }
    
    // 解包 {success, data} 格式
    const response: ApiResponse<BackendStockRecommend[]> = await res.json();
    
    if (!response.success || !response.data) {
      throw new Error("API returned unsuccessful response");
    }
    
    // 转换数据格式
    return response.data.map(mapStockFromBackend);
  } catch (error) {
    console.error("getStocks error, falling back to mock data:", error);
    return mockData.stocks.filter(
      (stock) =>
        stock.market === market &&
        stock.roe >= filters.roeMin &&
        stock.debtRatio <= filters.debtMax
    );
  }
}

/**
 * Fetch financial details with fallback to mock data.
 */
export async function getFinancials(code: string): Promise<FinancialRecord> {
  try {
    const res = await fetch(`/api/financials/${code}`, {
      next: { revalidate: 60 }
    });
    
    if (!res.ok) {
      throw new Error("Failed to fetch financials");
    }
    
    // 解包 {success, data} 格式
    const response: ApiResponse<BackendFinancialDetail | null> = await res.json();
    
    if (!response.success || !response.data) {
      throw new Error("API returned unsuccessful response");
    }
    
    // 转换数据格式
    return mapFinancialFromBackend(response.data);
  } catch (error) {
    console.error("getFinancials error, falling back to mock data:", error);
    return mockData.financials[code] ?? mockData.financials["600519"];
  }
}

/**
 * Fetch shareholder data with fallback to mock data.
 */
export async function getShareholders(code: string): Promise<ShareholderRecord> {
  try {
    const res = await fetch(`/api/shareholders/${code}`, {
      next: { revalidate: 60 }
    });
    
    if (!res.ok) {
      throw new Error("Failed to fetch shareholders");
    }
    
    // 解包 {success, data} 格式
    const response: ApiResponse<BackendShareholderDetail | null> = await res.json();
    
    if (!response.success || !response.data) {
      throw new Error("API returned unsuccessful response");
    }
    
    // 转换数据格式
    return mapShareholderFromBackend(response.data);
  } catch (error) {
    console.error("getShareholders error, falling back to mock data:", error);
    return mockData.shareholders[code] ?? mockData.shareholders["600519"];
  }
}
