"use client";

import { useEffect, useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Search, ArrowUpCircle, ArrowDownCircle, Filter, Calendar } from "lucide-react";
import { getShareholderChanges } from "@/lib/api";
import { ShareholderChangeItem } from "@/lib/types";
import { cn } from "@/lib/utils";

const STOCK_OPTIONS = [
  { code: "600519", company: "贵州茅台" },
  { code: "000858", company: "五粮液" },
  { code: "000333", company: "美的集团" },
  { code: "600036", company: "招商银行" },
  { code: "601318", company: "中国平安" },
];

const HOLDER_TYPES = ["全部", "机构", "个人", "基金", "社保", "QFII"];

function TimelineContent() {
  const searchParams = useSearchParams();
  const initialCode = searchParams.get("code") || "600519";

  const [selectedCode, setSelectedCode] = useState(initialCode);
  const [changes, setChanges] = useState<ShareholderChangeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [holderFilter, setHolderFilter] = useState("全部");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [format, setFormat] = useState<"card" | "text">("card");

  const filtered = useMemo(
    () =>
      STOCK_OPTIONS.filter(
        (item) =>
          item.company.includes(query) || item.code.includes(query)
      ),
    [query]
  );

  const filteredChanges = useMemo(() => {
    return changes.filter((c) => {
      if (dateFrom && (c.report_date || "") < dateFrom) return false;
      if (dateTo && (c.report_date || "") > dateTo) return false;
      return true;
    });
  }, [changes, dateFrom, dateTo]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getShareholderChanges(selectedCode);
        if (res.success && res.data) {
          setChanges(res.data.changes);
        } else {
          setChanges([]);
          setError("加载失败");
        }
      } catch {
        setChanges([]);
        setError("请求失败");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedCode]);

  const formatAmount = (val?: number) => {
    if (!val) return "-";
    if (val >= 100000000) return `${(val / 100000000).toFixed(2)}亿`;
    if (val >= 10000) return `${(val / 10000).toFixed(2)}万`;
    return `${val}`;
  };

  const selectedCompany = STOCK_OPTIONS.find((s) => s.code === selectedCode)?.company || "";

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-accent">Shareholder Timeline</p>
        <h1 className="mt-3 text-3xl font-semibold text-white tablet:text-4xl">
          持股变动时间线
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          追踪股东增减持变动历史，了解机构与重要股东的投资动向。
        </p>
      </section>

      {/* Search & Filters */}
      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel space-y-4">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            aria-label="搜索公司"
            className="w-full rounded-2xl border border-white/10 bg-slate-950/70 py-3 pl-11 pr-4 text-white outline-none placeholder:text-slate-500 focus:border-primary"
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索股票代码或公司名称"
            value={query}
          />
        </label>

        <div className="flex flex-wrap gap-2">
          {filtered.map((item) => (
            <button
              key={item.code}
              type="button"
              className={cn(
                "rounded-full border px-4 py-2 text-sm transition",
                selectedCode === item.code
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-white/10 text-slate-300 hover:bg-white/5"
              )}
              onClick={() => setSelectedCode(item.code)}
              disabled={loading}
            >
              {item.company}
            </button>
          ))}
        </div>

        {/* Advanced filters */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-white/5">
          <Filter className="h-4 w-4 text-slate-400" />
          <div className="flex flex-wrap gap-2">
            {HOLDER_TYPES.map((type) => (
              <button
                key={type}
                type="button"
                className={cn(
                  "rounded-full border px-3 py-1 text-xs transition",
                  holderFilter === type
                    ? "border-accent bg-accent/15 text-accent"
                    : "border-white/10 text-slate-400 hover:bg-white/5"
                )}
                onClick={() => setHolderFilter(type)}
              >
                {type}
              </button>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400" />
            <input
              type="date"
              className="rounded-lg border border-white/10 bg-slate-950/70 px-2 py-1 text-xs text-white outline-none"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
            <span className="text-xs text-slate-500">至</span>
            <input
              type="date"
              className="rounded-lg border border-white/10 bg-slate-950/70 px-2 py-1 text-xs text-white outline-none"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <h3 className="mb-4 text-lg font-semibold text-white">
          {selectedCompany} ({selectedCode}) 变动记录
          <span className="ml-2 text-sm font-normal text-slate-400">
            共 {filteredChanges.length} 条
          </span>
        </h3>

        {loading ? (
          <div className="flex h-40 items-center justify-center text-slate-400">加载中...</div>
        ) : error ? (
          <div className="flex h-40 items-center justify-center text-negative">{error}</div>
        ) : filteredChanges.length === 0 ? (
          <div className="flex h-40 items-center justify-center text-slate-400">暂无变动记录</div>
        ) : (
          <div className="relative space-y-0">
            {filteredChanges.map((record, index) => {
              const isIncrease = record.change_type === "increase" || record.change_type.includes("增");
              return (
                <div key={index} className="flex gap-4">
                  {/* Timeline line */}
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                        isIncrease ? "bg-positive/20" : "bg-negative/20"
                      )}
                    >
                      {isIncrease ? (
                        <ArrowUpCircle className="h-4 w-4 text-positive" />
                      ) : (
                        <ArrowDownCircle className="h-4 w-4 text-negative" />
                      )}
                    </div>
                    {index < filteredChanges.length - 1 && (
                      <div className="w-px flex-1 bg-white/10" />
                    )}
                  </div>

                  {/* Content card */}
                  <div
                    className={cn(
                      "mb-4 flex-1 rounded-2xl border p-4",
                      isIncrease
                        ? "border-positive/20 bg-positive/5"
                        : "border-negative/20 bg-negative/5"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-white">{record.holder_name}</span>
                      <span className="text-xs text-slate-400">{record.report_date || "-"}</span>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-sm">
                      <span
                        className={cn(
                          "font-medium",
                          isIncrease ? "text-positive" : "text-negative"
                        )}
                      >
                        {record.change_type}
                      </span>
                      {record.change_ratio !== undefined && (
                        <span className="text-slate-300">
                          比例: {record.change_ratio.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

export default function ShareholderTimelinePage() {
  return (
    <Suspense fallback={<div className="text-slate-400">加载中...</div>}>
      <TimelineContent />
    </Suspense>
  );
}
