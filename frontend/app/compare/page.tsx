"use client";

import { useState } from "react";
import { GitCompare, TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react";
import { compareStocks } from "@/lib/api";
import { StockCompareItem } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Stock comparison page.
 */
export default function ComparePage(): JSX.Element {
  const [codes, setCodes] = useState("");
  const [stocks, setStocks] = useState<StockCompareItem[]>([]);
  const [metrics, setMetrics] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!codes.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await compareStocks(codes.trim());
      if (response.success && response.stocks.length > 0) {
        setStocks(response.stocks);
        setMetrics(response.metrics);
      } else {
        setError("未找到对比数据，请检查股票代码");
        setStocks([]);
        setMetrics([]);
      }
    } catch (err) {
      console.error("Compare error:", err);
      setError("对比分析失败，请稍后重试");
      setStocks([]);
      setMetrics([]);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: number | undefined, suffix = ""): string => {
    if (value === undefined || value === null) return "-";
    return `${value.toFixed(2)}${suffix}`;
  };

  const formatLargeNumber = (value: number | undefined): string => {
    if (value === undefined || value === null) return "-";
    if (value >= 100000000) {
      return `${(value / 100000000).toFixed(2)}亿`;
    }
    if (value >= 10000) {
      return `${(value / 10000).toFixed(2)}万`;
    }
    return value.toFixed(2);
  };

  const getValueColor = (metric: string, value: number | undefined): string => {
    if (value === undefined || value === null) return "text-slate-400";
    
    // 对于 ROE、毛利率，越高越好
    if (["roe", "gross_margin"].includes(metric)) {
      return value >= 15 ? "text-green-400" : value >= 10 ? "text-yellow-400" : "text-red-400";
    }
    
    // 对于负债率，越低越好
    if (metric === "debt_ratio") {
      return value <= 40 ? "text-green-400" : value <= 60 ? "text-yellow-400" : "text-red-400";
    }
    
    // 对于营收、净利润增长
    if (["revenue", "net_profit"].includes(metric)) {
      return value > 0 ? "text-green-400" : value < 0 ? "text-red-400" : "text-slate-400";
    }
    
    return "text-white";
  };

  const metricLabels: Record<string, string> = {
    roe: "ROE (%)",
    debt_ratio: "负债率 (%)",
    gross_margin: "毛利率 (%)",
    revenue: "营收",
    net_profit: "净利润",
    eps: "EPS (元)",
  };

  const getMetricLabel = (metric: string): string => {
    return metricLabels[metric] || metric;
  };

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-primary">Stock Comparison</p>
        <h1 className="mt-3 text-3xl font-semibold text-white tablet:text-4xl">
          股票对比分析
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          输入多个股票代码（逗号分隔），横向对比财务指标
        </p>
      </section>

      {/* Input Section */}
      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <h2 className="mb-4 text-lg font-semibold text-white">输入股票代码</h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={codes}
            onChange={(e) => setCodes(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCompare()}
            placeholder="例如: 600519,000858,000333"
            className="flex-1 rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-primary focus:outline-none"
          />
          <button
            onClick={handleCompare}
            disabled={loading || !codes.trim()}
            className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-medium text-white transition hover:bg-primary/90 disabled:opacity-50"
          >
            <GitCompare className="h-4 w-4" />
            {loading ? "对比中..." : "开始对比"}
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          支持A股代码，多个代码用英文逗号分隔
        </p>
      </section>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 rounded-3xl border border-red-500/30 bg-red-500/10 p-5 text-red-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Comparison Table */}
      {stocks.length > 0 && (
        <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel overflow-x-auto">
          <h2 className="mb-4 text-lg font-semibold text-white">对比结果</h2>
          
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-white/10">
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                  指标
                </th>
                {stocks.map((stock) => (
                  <th key={stock.code} className="px-4 py-3 text-center text-sm font-medium text-white">
                    <div>
                      <span className="block">{stock.name}</span>
                      <span className="text-xs text-slate-500">{stock.code}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* ROE */}
              <tr className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-sm text-slate-300">ROE</td>
                {stocks.map((stock) => (
                  <td key={stock.code} className="px-4 py-3 text-center">
                    <span className={cn("text-sm font-medium", getValueColor("roe", stock.roe))}>
                      {formatValue(stock.roe, "%")}
                    </span>
                  </td>
                ))}
              </tr>
              
              {/* 负债率 */}
              <tr className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-sm text-slate-300">负债率</td>
                {stocks.map((stock) => (
                  <td key={stock.code} className="px-4 py-3 text-center">
                    <span className={cn("text-sm font-medium", getValueColor("debt_ratio", stock.debt_ratio))}>
                      {formatValue(stock.debt_ratio, "%")}
                    </span>
                  </td>
                ))}
              </tr>
              
              {/* 毛利率 */}
              <tr className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-sm text-slate-300">毛利率</td>
                {stocks.map((stock) => (
                  <td key={stock.code} className="px-4 py-3 text-center">
                    <span className={cn("text-sm font-medium", getValueColor("gross_margin", stock.gross_margin))}>
                      {formatValue(stock.gross_margin, "%")}
                    </span>
                  </td>
                ))}
              </tr>
              
              {/* 营收 */}
              <tr className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-sm text-slate-300">营收</td>
                {stocks.map((stock) => (
                  <td key={stock.code} className="px-4 py-3 text-center">
                    <span className={cn("text-sm font-medium", getValueColor("revenue", stock.revenue))}>
                      {formatLargeNumber(stock.revenue)}
                    </span>
                  </td>
                ))}
              </tr>
              
              {/* 净利润 */}
              <tr className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-sm text-slate-300">净利润</td>
                {stocks.map((stock) => (
                  <td key={stock.code} className="px-4 py-3 text-center">
                    <span className={cn("text-sm font-medium", getValueColor("net_profit", stock.net_profit))}>
                      {formatLargeNumber(stock.net_profit)}
                    </span>
                  </td>
                ))}
              </tr>
              
              {/* EPS */}
              <tr className="hover:bg-white/5">
                <td className="px-4 py-3 text-sm text-slate-300">EPS</td>
                {stocks.map((stock) => (
                  <td key={stock.code} className="px-4 py-3 text-center">
                    <span className="text-sm font-medium text-white">
                      {formatValue(stock.eps)}
                    </span>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
          
          {/* Legend */}
          <div className="mt-6 flex flex-wrap gap-4 border-t border-white/10 pt-4 text-xs">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-3 w-3 text-green-400" />
              <span className="text-slate-400">优秀</span>
            </div>
            <div className="flex items-center gap-2">
              <Minus className="h-3 w-3 text-yellow-400" />
              <span className="text-slate-400">一般</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-3 w-3 text-red-400" />
              <span className="text-slate-400">较差</span>
            </div>
          </div>
        </section>
      )}

      {/* Empty State */}
      {!loading && !error && stocks.length === 0 && (
        <div className="rounded-3xl border border-white/10 bg-card/80 p-12 text-center">
          <GitCompare className="mx-auto h-16 w-16 text-slate-600 mb-4" />
          <p className="text-slate-400">输入股票代码开始对比分析</p>
        </div>
      )}
    </div>
  );
}
