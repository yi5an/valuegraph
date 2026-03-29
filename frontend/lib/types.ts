/**
 * Shared domain types for ValueGraph frontend.
 */
export type Market = "A股" | "美股" | "港股";

export interface Stock {
  code: string;
  name: string;
  market: Market;
  price: number;
  changePercent: number;
  roe: number;
  debtRatio: number;
  pe: number;
  reason: string;
  tags: string[];
}

export interface StockFilters {
  roeMin: number;
  debtMax: number;
}

export interface FinancialMetricCard {
  label: string;
  value: string;
  tone: "positive" | "negative" | "neutral";
}

export interface FinancialHistoryPoint {
  year: string;
  revenue: number;
  netProfit: number;
  roe: number;
  grossMargin: number;
  cashFlow: number;
}

export interface FinancialHealthPoint {
  subject: string;
  score: number;
  fullMark: number;
}

export interface FinancialRecord {
  code: string;
  company: string;
  metrics: FinancialMetricCard[];
  history: FinancialHistoryPoint[];
  health: FinancialHealthPoint[];
}

export interface ShareholderRow {
  rank: number;
  name: string;
  shares: string;
  ratio: string;
  change: string;
}

export interface InstitutionHolding {
  institution: string;
  position: string;
  ratio: string;
  action: string;
}

export interface OwnershipSlice {
  name: string;
  value: number;
}

export interface ShareholderRecord {
  code: string;
  company: string;
  ownership: OwnershipSlice[];
  topHolders: ShareholderRow[];
  institutions: InstitutionHolding[];
}

export interface NewsItem {
  id: number;
  title: string;
  content: string;
  source: string;
  stock_code: string | null;
  keywords: string | null;
  published_at: string;
  url: string;
}

export interface NewsResponse {
  success: boolean;
  data: NewsItem[] | null;
}

// Knowledge Graph types
export interface KGNode {
  id: string;
  name: string;
  type: string;  // company, person, stock, industry, event
  properties: Record<string, any>;
}

export interface KGEdge {
  source: string;
  target: string;
  type: string;  // RELATED_TO, invests_in, supplies_to, competes_with
  properties: Record<string, any>;
}

export interface KGResponse {
  success: boolean;
  data: { nodes: KGNode[]; edges: KGEdge[] } | null;
}

// Wave 2 新增类型
export interface CompareResponse {
  success: boolean;
  stocks: StockCompareItem[];
  total: number;
  metrics: string[];
}

export interface StockCompareItem {
  code: string;
  name: string;
  market: string;
  roe?: number;
  debt_ratio?: number;
  gross_margin?: number;
  revenue?: number;
  net_profit?: number;
  eps?: number;
}

export interface AnomalyResponse {
  success: boolean;
  data: { has_anomaly: boolean; anomalies: AnomalyItem[] };
}

export interface AnomalyItem {
  type: string;
  description: string;
  severity: string;
}

export interface InfluenceResponse {
  success: boolean;
  data: InfluenceItem[];
  total: number;
}

export interface InfluenceItem {
  name: string;
  score: number;
  type: string;
}

export interface ShareholderChangeResponse {
  success: boolean;
  data: {
    stock_code: string;
    changes: ShareholderChangeItem[];
  };
}

export interface ShareholderChangeItem {
  holder_name: string;
  change_type: string;
  change_ratio?: number;
  report_date?: string;
}

export interface NewsItemWithSentiment extends NewsItem {
  sentiment?: "positive" | "negative" | "neutral";
}
