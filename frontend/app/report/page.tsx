"use client";

import { useEffect, useState } from "react";
import {
  BarChart3, TrendingUp, Newspaper, ClipboardList
} from "lucide-react";

interface DailyReport {
  success: boolean;
  data?: {
    date: string;
    market_overview?: {
      index_name: string;
      close: number;
      change_percent: number;
      volume?: string;
    }[];
    portfolio_focus?: {
      stock_code: string;
      name: string;
      close: number;
      change_percent: number;
      reason?: string;
    }[];
    policy_news?: {
      title: string;
      source: string;
      summary?: string;
    }[];
    data_summary?: {
      key: string;
      value: string;
      note?: string;
    }[];
  };
}

export default function ReportPage() {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [format, setFormat] = useState<"card" | "text">("card");

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const res = await fetch("/api/stats/daily-report");
        const json: DailyReport = await res.json();
        setReport(json);
      } catch {
        setReport(null);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        加载每日早报...
      </div>
    );
  }

  if (!report?.success || !report.data) {
    return (
      <div className="flex h-64 items-center justify-center text-negative">
        暂无早报数据
      </div>
    );
  }

  const { data } = report;

  const toggleButtons = (
    <div className="flex items-center gap-2">
      <button
        type="button"
        className={`rounded-full border px-3 py-1.5 text-xs ${
          format === "card" ? "border-primary bg-primary/15 text-primary" : "border-white/10 text-slate-400"
        }`}
        onClick={() => setFormat("card")}
      >
        卡片
      </button>
      <button
        type="button"
        className={`rounded-full border px-3 py-1.5 text-xs ${
          format === "text" ? "border-primary bg-primary/15 text-primary" : "border-white/10 text-slate-400"
        }`}
        onClick={() => setFormat("text")}
      >
        文本
      </button>
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-accent">Daily Report</p>
            <h1 className="mt-3 text-3xl font-semibold text-white tablet:text-4xl">每日早报</h1>
            <p className="mt-2 text-sm text-slate-400">{data.date}</p>
          </div>
          {toggleButtons}
        </div>
      </section>

      {format === "text" ? (
        <section className="rounded-3xl border border-white/10 bg-card/80 p-6 shadow-panel">
          <p className="text-xs text-slate-400 mb-4">📅 {data.date}</p>
          <pre className="whitespace-pre-wrap text-sm leading-7 text-slate-200">
            {JSON.stringify(data, null, 2)}
          </pre>
        </section>
      ) : (
        <>
          {/* Market Overview */}
          {data.market_overview && data.market_overview.length > 0 && (
            <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <TrendingUp className="h-5 w-5 text-primary" />
                市场概览
              </h3>
              <div className="grid gap-3 tablet:grid-cols-2 desktop:grid-cols-4">
                {data.market_overview.map((item, i) => (
                  <div key={i} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="text-sm text-slate-400">{item.index_name}</p>
                    <p className="mt-1 text-xl font-semibold text-white">{item.close.toFixed(2)}</p>
                    <p className={`mt-1 text-sm ${item.change_percent >= 0 ? "text-positive" : "text-negative"}`}>
                      {item.change_percent >= 0 ? "+" : ""}{item.change_percent.toFixed(2)}%
                    </p>
                    {item.volume && <p className="mt-1 text-xs text-slate-500">{item.volume}</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Portfolio Focus */}
          {data.portfolio_focus && data.portfolio_focus.length > 0 && (
            <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <BarChart3 className="h-5 w-5 text-accent" />
                持仓关注
              </h3>
              <div className="space-y-3">
                {data.portfolio_focus.map((item, i) => (
                  <div key={i} className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-400">{item.stock_code}</span>
                      <span className="font-medium text-white">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-white">{item.close.toFixed(2)}</p>
                      <p className={`text-sm ${item.change_percent >= 0 ? "text-positive" : "text-negative"}`}>
                        {item.change_percent >= 0 ? "+" : ""}{item.change_percent.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Policy News */}
          {data.policy_news && data.policy_news.length > 0 && (
            <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <Newspaper className="h-5 w-5 text-yellow-400" />
                政策要闻
              </h3>
              <div className="space-y-3">
                {data.policy_news.map((item, i) => (
                  <div key={i} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <div className="flex items-start justify-between">
                      <h4 className="font-medium text-white">{item.title}</h4>
                      <span className="shrink-0 rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-400">
                        {item.source}
                      </span>
                    </div>
                    {item.summary && (
                      <p className="mt-2 text-sm text-slate-300">{item.summary}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Data Summary */}
          {data.data_summary && data.data_summary.length > 0 && (
            <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <ClipboardList className="h-5 w-5 text-purple-400" />
                数据摘要
              </h3>
              <div className="grid gap-3 tablet:grid-cols-2 desktop:grid-cols-3">
                {data.data_summary.map((item, i) => (
                  <div key={i} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="text-xs text-slate-400">{item.key}</p>
                    <p className="mt-1 text-lg font-semibold text-white">{item.value}</p>
                    {item.note && <p className="mt-1 text-xs text-slate-500">{item.note}</p>}
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
