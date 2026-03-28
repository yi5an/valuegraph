"use client";

import { useMemo, useState, useEffect } from "react";
import { Search } from "lucide-react";
import { getFinancials } from "@/lib/api";
import { FinancialRecord } from "@/lib/types";
import { FinancialChart } from "@/components/FinancialChart";
import { RadarChart } from "@/components/RadarChart";
import { cn } from "@/lib/utils";

// 预定义的股票列表（用于搜索建议）
const STOCK_OPTIONS = [
  { code: "600519", company: "贵州茅台" },
  { code: "000858", company: "五粮液" },
  { code: "000333", company: "美的集团" },
  { code: "600036", company: "招商银行" },
  { code: "601318", company: "中国平安" },
  { code: "000001", company: "平安银行" },
];

/**
 * Client financial analysis page with autocomplete and API integration.
 */
export function ClientFinancialPage({
  initialData
}: {
  initialData: FinancialRecord;
}): JSX.Element {
  const [query, setQuery] = useState(initialData.company);
  const [current, setCurrent] = useState<FinancialRecord>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filtered = useMemo(
    () =>
      STOCK_OPTIONS.filter(
        (item) =>
          item.company.toLowerCase().includes(query.toLowerCase()) ||
          item.code.toLowerCase().includes(query.toLowerCase())
      ),
    [query]
  );

  // 当选择新股票时，从 API 获取数据
  const handleStockSelect = async (code: string, company: string) => {
    setQuery(company);
    setLoading(true);
    setError(null);

    try {
      const data = await getFinancials(code);
      setCurrent(data);
    } catch (err) {
      console.error("Failed to load financials:", err);
      setError("加载财报数据失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-accent">Financial Analytics</p>
        <h1 className="mt-3 text-3xl font-semibold text-white tablet:text-4xl">
          财报指标、趋势图与健康度雷达集中展示
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          本分析基于价值投资，不构成买卖推荐。选择股票代码查看详细财报数据。
        </p>
      </section>

      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            aria-label="搜索公司"
            className="w-full rounded-2xl border border-white/10 bg-slate-950/70 py-3 pl-11 pr-4 text-white outline-none ring-0 placeholder:text-slate-500 focus:border-primary"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索股票代码或公司名称"
            value={query}
          />
        </label>

        <div className="mt-4 flex flex-wrap gap-2">
          {filtered.map((item) => (
            <button
              key={item.code}
              aria-label={`选择${item.company}`}
              className={cn(
                "rounded-full border px-4 py-2 text-sm",
                current.code === item.code
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-white/10 text-slate-300"
              )}
              onClick={() => handleStockSelect(item.code, item.company)}
              disabled={loading}
              type="button"
            >
              {item.company}
            </button>
          ))}
        </div>
      </section>

      {loading && (
        <div className="rounded-3xl border border-white/10 bg-card/80 p-8 text-slate-300">
          加载财报数据中...
        </div>
      )}

      {error && (
        <div className="rounded-3xl border border-negative/30 bg-negative/10 p-8 text-negative">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <section className="grid gap-4 tablet:grid-cols-2 desktop:grid-cols-3">
            {current.metrics.map((metric) => (
              <article
                key={metric.label}
                className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel"
              >
                <p className="text-sm text-slate-400">{metric.label}</p>
                <p
                  className={cn(
                    "mt-3 text-2xl font-semibold",
                    metric.tone === "positive" && "text-positive",
                    metric.tone === "negative" && "text-negative",
                    metric.tone === "neutral" && "text-white"
                  )}
                >
                  {metric.value}
                </p>
              </article>
            ))}
          </section>

          <div className="grid gap-6 desktop:grid-cols-[1.5fr_1fr]">
            <FinancialChart data={current.history} />
            <RadarChart data={current.health} />
          </div>
        </>
      )}
    </div>
  );
}
