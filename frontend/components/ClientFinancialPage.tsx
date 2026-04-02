"use client";

import { useMemo, useState, useEffect } from "react";
import { Search, AlertTriangle, AlertCircle, Info } from "lucide-react";
import { getFinancials, getAnomalies } from "@/lib/api";
import { FinancialRecord, AnomalyItem } from "@/lib/types";
import { FinancialChart } from "@/components/FinancialChart";
import { RadarChart } from "@/components/RadarChart";
import { DupontChart } from "@/components/DupontChart";
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
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [hasAnomaly, setHasAnomaly] = useState(false);
  const [loadingAnomalies, setLoadingAnomalies] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "dupont">("overview");

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
    setLoadingAnomalies(true);

    try {
      const data = await getFinancials(code);
      setCurrent(data);
      
      // 同时获取异常检测
      const anomalyResponse = await getAnomalies(code);
      setHasAnomaly(anomalyResponse.data?.has_anomaly || false);
      setAnomalies(anomalyResponse.data?.anomalies || []);
    } catch (err) {
      console.error("Failed to load financials:", err);
      setError("加载财报数据失败");
    } finally {
      setLoading(false);
      setLoadingAnomalies(false);
    }
  };
  
  // 初始化时也获取异常
  useEffect(() => {
    const fetchInitialAnomalies = async () => {
      const anomalyResponse = await getAnomalies(initialData.code);
      setHasAnomaly(anomalyResponse.data?.has_anomaly || false);
      setAnomalies(anomalyResponse.data?.anomalies || []);
    };
    fetchInitialAnomalies();
  }, [initialData.code]);

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

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          type="button"
          className={cn(
            "rounded-full border px-5 py-2 text-sm transition",
            activeTab === "overview"
              ? "border-primary bg-primary/15 text-primary"
              : "border-white/10 text-slate-300 hover:bg-white/5"
          )}
          onClick={() => setActiveTab("overview")}
        >
          综合概览
        </button>
        <button
          type="button"
          className={cn(
            "rounded-full border px-5 py-2 text-sm transition",
            activeTab === "dupont"
              ? "border-primary bg-primary/15 text-primary"
              : "border-white/10 text-slate-300 hover:bg-white/5"
          )}
          onClick={() => setActiveTab("dupont")}
        >
          杜邦分析
        </button>
      </div>

      {activeTab === "dupont" ? (
        <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
          <DupontChart />
        </section>
      ) : (
      <>
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

          {/* 异常检测区域 */}
          <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                财报异常检测
              </h3>
              {hasAnomaly && (
                <span className="rounded-full bg-red-500/20 px-3 py-1 text-xs font-medium text-red-400">
                  发现异常
                </span>
              )}
            </div>
            
            {loadingAnomalies ? (
              <div className="text-sm text-slate-400">检测中...</div>
            ) : anomalies.length > 0 ? (
              <div className="space-y-3">
                {anomalies.map((anomaly, index) => (
                  <div
                    key={index}
                    className={cn(
                      "rounded-xl border p-4",
                      anomaly.severity === "high" && "border-red-500/30 bg-red-500/10",
                      anomaly.severity === "medium" && "border-yellow-500/30 bg-yellow-500/10",
                      anomaly.severity === "low" && "border-blue-500/30 bg-blue-500/10"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {anomaly.severity === "high" ? (
                        <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 shrink-0" />
                      ) : anomaly.severity === "medium" ? (
                        <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5 shrink-0" />
                      ) : (
                        <Info className="h-5 w-5 text-blue-400 mt-0.5 shrink-0" />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white">{anomaly.type}</span>
                          <span className={cn(
                            "text-xs px-2 py-0.5 rounded",
                            anomaly.severity === "high" && "bg-red-500/20 text-red-400",
                            anomaly.severity === "medium" && "bg-yellow-500/20 text-yellow-400",
                            anomaly.severity === "low" && "bg-blue-500/20 text-blue-400"
                          )}>
                            {anomaly.severity === "high" ? "高" : anomaly.severity === "medium" ? "中" : "低"}
                          </span>
                        </div>
                        <p className="text-sm text-slate-300">{anomaly.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-sm text-green-400">
                <Info className="h-4 w-4" />
                未发现明显异常
              </div>
            )}
          </section>
        </>
      )}
      </>
      )}
    </div>
  );
}
