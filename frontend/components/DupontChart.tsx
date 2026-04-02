"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from "recharts";

interface DupontQuarter {
  report_date: string;
  roe: number;
  net_profit_margin: number;
  asset_turnover: number;
  equity_multiplier: number;
}

interface DupontResponse {
  success: boolean;
  data?: {
    stock_code: string;
    name: string;
    quarters: DupontQuarter[];
  };
}

const COLORS = {
  roe: "#2563EB",
  margin: "#10B981",
  turnover: "#F97316",
  multiplier: "#A855F7",
};

const STOCK_OPTIONS = [
  { code: "600519", company: "贵州茅台" },
  { code: "000858", company: "五粮液" },
  { code: "000333", company: "美的集团" },
  { code: "600036", company: "招商银行" },
  { code: "601318", company: "中国平安" },
];

export function DupontChart(): JSX.Element {
  const [selectedCode, setSelectedCode] = useState("600519");
  const [data, setData] = useState<DupontQuarter[]>([]);
  const [loading, setLoading] = useState(false);
  const [companyName, setCompanyName] = useState("");

  useEffect(() => {
    const fetchDupont = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/financials/${selectedCode}/dupont`);
        const json: DupontResponse = await res.json();
        if (json.success && json.data) {
          setData(json.data.quarters);
          setCompanyName(json.data.name);
        } else {
          setData([]);
          setCompanyName("");
        }
      } catch {
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchDupont();
  }, [selectedCode]);

  const formatValue = (val: number) => `${val.toFixed(2)}%`;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {STOCK_OPTIONS.map((item) => (
          <button
            key={item.code}
            type="button"
            className={`rounded-full border px-4 py-2 text-sm transition ${
              selectedCode === item.code
                ? "border-primary bg-primary/15 text-primary"
                : "border-white/10 text-slate-300 hover:bg-white/5"
            }`}
            onClick={() => setSelectedCode(item.code)}
          >
            {item.company}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center text-slate-400">
          加载杜邦分析数据...
        </div>
      ) : data.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-slate-400">
          暂无杜邦分析数据
        </div>
      ) : (
        <>
          {/* ROE 拆解卡片 */}
          <div className="grid grid-cols-2 gap-3 tablet:grid-cols-4">
            {(["roe", "net_profit_margin", "asset_turnover", "equity_multiplier"] as const).map((key) => {
              const latest = data[0];
              const prev = data[1];
              const value = latest?.[key] ?? 0;
              const prevValue = prev?.[key] ?? 0;
              const diff = value - prevValue;
              const labels: Record<string, string> = {
                roe: "ROE",
                net_profit_margin: "净利率",
                asset_turnover: "总资产周转率",
                equity_multiplier: "权益乘数",
              };
              const colors: Record<string, string> = {
                roe: COLORS.roe,
                net_profit_margin: COLORS.margin,
                asset_turnover: COLORS.turnover,
                equity_multiplier: COLORS.multiplier,
              };
              return (
                <div
                  key={key}
                  className="rounded-2xl border border-white/10 bg-slate-950/70 p-4"
                >
                  <p className="text-xs text-slate-400">{labels[key]}</p>
                  <p className="mt-1 text-xl font-semibold text-white">
                    {formatValue(value)}
                  </p>
                  {data.length > 1 && (
                    <p
                      className={`mt-1 text-xs ${
                        diff >= 0 ? "text-positive" : "text-negative"
                      }`}
                    >
                      {diff >= 0 ? "↑" : "↓"} {Math.abs(diff).toFixed(2)}%
                    </p>
                  )}
                  <div
                    className="mt-2 h-1 rounded-full"
                    style={{ backgroundColor: colors[key] + "33" }}
                  >
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(value * 3, 100)}%`,
                        backgroundColor: colors[key],
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* 趋势图 */}
          <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <h4 className="mb-3 text-sm font-medium text-slate-300">
              {companyName} 杜邦分析趋势（ROE = 净利率 × 周转率 × 权益乘数）
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[...data].reverse()} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="report_date" tick={{ fill: "#94A3B8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94A3B8", fontSize: 12 }} tickFormatter={(v: number) => `${v}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#111827", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px" }}
                  labelStyle={{ color: "#e2e8f0" }}
                  formatter={(value: number) => [`${value.toFixed(2)}%`, ""]}
                />
                <Legend
                  formatter={(value: string) => {
                    const map: Record<string, string> = { roe: "ROE", net_profit_margin: "净利率", asset_turnover: "周转率", equity_multiplier: "权益乘数" };
                    return map[value] || value;
                  }}
                />
                <Bar dataKey="roe" fill={COLORS.roe} radius={[4, 4, 0, 0]} />
                <Bar dataKey="net_profit_margin" fill={COLORS.margin} radius={[4, 4, 0, 0]} />
                <Bar dataKey="asset_turnover" fill={COLORS.turnover} radius={[4, 4, 0, 0]} />
                <Bar dataKey="equity_multiplier" fill={COLORS.multiplier} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 公式说明 */}
          <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <h4 className="text-sm font-medium text-slate-300 mb-2">杜邦分析公式</h4>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="rounded-lg bg-blue-500/20 px-3 py-1 font-medium text-blue-400">ROE</span>
              <span className="text-slate-400">=</span>
              <span className="rounded-lg bg-green-500/20 px-3 py-1 font-medium text-green-400">净利率</span>
              <span className="text-slate-400">×</span>
              <span className="rounded-lg bg-orange-500/20 px-3 py-1 font-medium text-orange-400">总资产周转率</span>
              <span className="text-slate-400">×</span>
              <span className="rounded-lg bg-purple-500/20 px-3 py-1 font-medium text-purple-400">权益乘数</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
