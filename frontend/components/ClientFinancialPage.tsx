"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { mockData } from "@/lib/mockData";
import { FinancialRecord } from "@/lib/types";
import { FinancialChart } from "@/components/FinancialChart";
import { RadarChart } from "@/components/RadarChart";
import { cn } from "@/lib/utils";

/**
 * Client financial analysis page with mock autocomplete.
 */
export function ClientFinancialPage({
  initialData
}: {
  initialData: FinancialRecord;
}): JSX.Element {
  const options = useMemo(
    () =>
      Object.values(mockData.financials).map((item) => ({
        code: item.code,
        company: item.company
      })),
    []
  );
  const [query, setQuery] = useState(initialData.company);
  const [current, setCurrent] = useState<FinancialRecord>(initialData);

  const filtered = useMemo(
    () =>
      options.filter(
        (item) =>
          item.company.toLowerCase().includes(query.toLowerCase()) ||
          item.code.toLowerCase().includes(query.toLowerCase())
      ),
    [options, query]
  );

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-accent">Financial Analytics</p>
        <h1 className="mt-3 text-3xl font-semibold text-white tablet:text-4xl">
          财报指标、趋势图与健康度雷达集中展示
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          本分析基于价值投资，不构成买卖推荐。当前搜索使用模拟自动补全数据，后续可直接接后端接口。
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
              onClick={() => {
                setCurrent(mockData.financials[item.code]);
                setQuery(item.company);
              }}
              type="button"
            >
              {item.company}
            </button>
          ))}
        </div>
      </section>

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
    </div>
  );
}
