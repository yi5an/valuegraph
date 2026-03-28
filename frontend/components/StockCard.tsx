"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Stock } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StockCardProps {
  stock: Stock;
}

/**
 * Stock summary card with expandable reason section.
 */
export function StockCard({ stock }: StockCardProps): JSX.Element {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="card-hover rounded-3xl border border-white/10 bg-card/85 p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-lg font-semibold text-white">{stock.name}</p>
          <p className="mt-1 text-sm text-slate-400">
            {stock.code} · {stock.market}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xl font-semibold text-white">{stock.price}</p>
          <p
            className={cn(
              "text-sm font-medium",
              stock.changePercent >= 0 ? "text-positive" : "text-negative"
            )}
          >
            {stock.changePercent >= 0 ? "+" : ""}
            {stock.changePercent.toFixed(2)}%
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-2xl bg-white/5 p-3">
          <p className="text-slate-400">ROE</p>
          <p className="mt-2 font-semibold text-positive">{stock.roe}%</p>
        </div>
        <div className="rounded-2xl bg-white/5 p-3">
          <p className="text-slate-400">负债率</p>
          <p
            className={cn(
              "mt-2 font-semibold",
              stock.debtRatio <= 50 ? "text-positive" : "text-negative"
            )}
          >
            {stock.debtRatio}%
          </p>
        </div>
        <div className="rounded-2xl bg-white/5 p-3">
          <p className="text-slate-400">PE</p>
          <p className={cn("mt-2 font-semibold", stock.pe <= 20 ? "text-positive" : "text-slate-100")}>
            {stock.pe}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {stock.tags.map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs text-primary"
          >
            {tag}
          </span>
        ))}
      </div>

      <button
        aria-label={expanded ? "收起推荐理由" : "展开推荐理由"}
        className="mt-4 flex w-full items-center justify-between rounded-2xl bg-white/5 px-4 py-3 text-left text-sm text-slate-200"
        onClick={() => setExpanded((value) => !value)}
        type="button"
      >
        <span>{stock.reason}</span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded ? (
        <p className="mt-3 text-sm leading-6 text-slate-300">
          重点关注盈利质量、资产负债结构与估值区间，当前模型认为该标的具备较强价值属性。
        </p>
      ) : null}
    </article>
  );
}
