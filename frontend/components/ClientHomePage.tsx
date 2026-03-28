"use client";

import { useEffect, useMemo, useState } from "react";
import { FilterPanel } from "@/components/FilterPanel";
import { StockCard } from "@/components/StockCard";
import { markets } from "@/lib/mockData";
import { getStocks } from "@/lib/api";
import { Stock, StockFilters } from "@/lib/types";

/**
 * Client container for homepage interactions.
 */
export function ClientHomePage(): JSX.Element {
  const [market, setMarket] = useState<(typeof markets)[number]>("A股");
  const [filters, setFilters] = useState<StockFilters>({ roeMin: 15, debtMax: 50 });
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    getStocks(market, filters)
      .then((result) => {
        if (!active) {
          return;
        }
        setStocks(result);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("股票列表加载失败");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [filters, market]);

  const emptyText = useMemo(() => {
    if (loading || error) {
      return null;
    }
    return stocks.length === 0 ? "当前筛选条件下暂无结果。" : null;
  }, [error, loading, stocks.length]);

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-primary">Value Investing</p>
        <h1 className="mt-3 max-w-2xl text-3xl font-semibold text-white tablet:text-5xl">
          聚焦高 ROE、低负债与可解释推荐的价值筛选工作台
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 tablet:text-base">
          本分析基于价值投资，不构成买卖推荐。使用统一筛选器快速比较 A 股、美股、港股候选标的。
        </p>
      </section>

      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <div className="flex flex-wrap gap-3">
          {markets.map((item) => (
            <button
              key={item}
              aria-label={`切换到${item}`}
              className={`rounded-full px-5 py-2 text-sm ${
                market === item
                  ? "bg-primary text-white"
                  : "border border-white/10 text-slate-300"
              }`}
              onClick={() => setMarket(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <FilterPanel filters={filters} onChange={setFilters} />

      {loading ? <div className="rounded-3xl border border-white/10 bg-card/80 p-8 text-slate-300">加载股票列表中...</div> : null}
      {error ? <div className="rounded-3xl border border-negative/30 bg-negative/10 p-8 text-negative">{error}</div> : null}
      {emptyText ? <div className="rounded-3xl border border-white/10 bg-card/80 p-8 text-slate-300">{emptyText}</div> : null}

      {!loading && !error && stocks.length > 0 ? (
        <section className="grid gap-5 tablet:grid-cols-2 desktop:grid-cols-3">
          {stocks.map((stock) => (
            <StockCard key={stock.code} stock={stock} />
          ))}
        </section>
      ) : null}
    </div>
  );
}
