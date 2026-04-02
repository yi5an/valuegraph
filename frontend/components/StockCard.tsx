"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Stock } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StockCardProps {
  stock: Stock;
}

/** Extract the first line (grade + name) from the reason text */
function getGradeLine(reason: string): string {
  const firstNewline = reason.indexOf("\n");
  return firstNewline > 0 ? reason.substring(0, firstNewline) : reason;
}

const sentimentColor: Record<string, string> = {
  正面: "bg-positive",
  负面: "bg-negative",
  中性: "bg-slate-400",
};

function ReasonSections({ sections }: { sections: NonNullable<Stock["reasonSections"]> }) {
  return (
    <div className="mt-3 flex flex-col gap-2">
      {/* 📊 基本面 */}
      {sections.fundamentals && (
        <div
          className="rounded-xl bg-white/5 p-3"
          style={{ borderLeft: "3px solid #10B981" }}
        >
          <p className="mb-1 text-xs font-medium text-slate-400">📊 基本面</p>
          <p className="whitespace-pre-line text-sm leading-6 text-slate-200">
            {sections.fundamentals}
          </p>
        </div>
      )}

      {/* 📈 动态信号 */}
      {sections.market_signals && (
        <div
          className="rounded-xl bg-orange-500/5 p-3"
          style={{ borderLeft: "3px solid #F97316" }}
        >
          <p className="mb-1 text-xs font-medium text-slate-400">📈 动态信号</p>
          <p className="whitespace-pre-line text-sm leading-6 text-slate-200">
            {sections.market_signals}
          </p>
        </div>
      )}

      {/* 📰 相关新闻 */}
      {sections.related_news && sections.related_news.length > 0 && (
        <div
          className="rounded-xl bg-white/5 p-3"
          style={{ borderLeft: "3px solid #2563EB" }}
        >
          <p className="mb-2 text-xs font-medium text-slate-400">📰 相关新闻</p>
          <ul className="flex flex-col gap-1.5">
            {sections.related_news.map((news, i) => (
              <li key={i} className="flex items-start gap-2 text-sm leading-6 text-slate-200">
                <span
                  className={cn(
                    "mt-2 h-2 w-2 shrink-0 rounded-full",
                    sentimentColor[news.sentiment] || "bg-slate-400"
                  )}
                />
                <span className="whitespace-pre-line">{news.title}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 💡 投资逻辑 */}
      {sections.investment_logic && (
        <div
          className="rounded-xl bg-primary/5 p-3"
          style={{ borderLeft: "3px solid #2563EB" }}
        >
          <p className="mb-1 text-xs font-medium text-slate-400">💡 投资逻辑</p>
          <p className="whitespace-pre-line text-sm leading-6 text-slate-200">
            {sections.investment_logic}
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Stock summary card with expandable reason section.
 */
export function StockCard({ stock }: StockCardProps): JSX.Element {
  const [expanded, setExpanded] = useState(false);

  const gradeLine = getGradeLine(stock.reason);
  const hasSections = !!stock.reasonSections;

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
        <span className="line-clamp-1">{gradeLine}</span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded &&
        (hasSections ? (
          <ReasonSections sections={stock.reasonSections!} />
        ) : (
          <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-300">
            {stock.reason}
          </p>
        ))}
    </article>
  );
}
