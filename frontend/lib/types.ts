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
