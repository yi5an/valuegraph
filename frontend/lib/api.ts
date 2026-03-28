import { mockData } from "@/lib/mockData";
import {
  FinancialRecord,
  ShareholderRecord,
  Stock,
  StockFilters
} from "@/lib/types";

const API_BASE = "http://localhost:8001/api";

/**
 * Fetch stock recommendations with fallback to mock data.
 */
export async function getStocks(
  market: string,
  filters: StockFilters
): Promise<Stock[]> {
  try {
    const params = new URLSearchParams({
      market,
      roeMin: String(filters.roeMin),
      debtMax: String(filters.debtMax)
    });
    const res = await fetch(`${API_BASE}/stocks/recommend?${params.toString()}`, {
      next: { revalidate: 60 }
    });
    if (!res.ok) {
      throw new Error("Failed to fetch stock list");
    }
    return (await res.json()) as Stock[];
  } catch {
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
    const res = await fetch(`${API_BASE}/financials/${code}`, {
      next: { revalidate: 60 }
    });
    if (!res.ok) {
      throw new Error("Failed to fetch financials");
    }
    return (await res.json()) as FinancialRecord;
  } catch {
    return mockData.financials[code] ?? mockData.financials["600519"];
  }
}

/**
 * Fetch shareholder data with fallback to mock data.
 */
export async function getShareholders(code: string): Promise<ShareholderRecord> {
  try {
    const res = await fetch(`${API_BASE}/shareholders/${code}`, {
      next: { revalidate: 60 }
    });
    if (!res.ok) {
      throw new Error("Failed to fetch shareholders");
    }
    return (await res.json()) as ShareholderRecord;
  } catch {
    return mockData.shareholders[code] ?? mockData.shareholders["600519"];
  }
}
