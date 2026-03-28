"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { FinancialHistoryPoint } from "@/lib/types";

interface FinancialChartProps {
  data: FinancialHistoryPoint[];
}

const metricOptions = [
  { label: "营收", key: "revenue" },
  { label: "净利润", key: "netProfit" },
  { label: "ROE", key: "roe" },
  { label: "毛利率", key: "grossMargin" },
  { label: "现金流", key: "cashFlow" }
] as const;

/**
 * Financial trend chart with range and metric selectors.
 */
export function FinancialChart({ data }: FinancialChartProps): JSX.Element {
  const [range, setRange] = useState<5 | 7 | 10>(5);
  const [metric, setMetric] =
    useState<(typeof metricOptions)[number]["key"]>("revenue");

  const displayData = useMemo(() => {
    if (data.length <= range) {
      return data;
    }
    return data.slice(data.length - range);
  }, [data, range]);

  return (
    <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
      <div className="flex flex-col gap-4 tablet:flex-row tablet:items-center tablet:justify-between">
        <div>
          <p className="text-lg font-semibold text-white">财务时间线</p>
          <p className="mt-1 text-sm text-slate-400">查看历史趋势并切换核心指标。</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {[5, 7, 10].map((item) => (
            <button
              key={item}
              aria-label={`查看 ${item} 年数据`}
              className={`rounded-full px-4 py-2 text-sm ${
                range === item
                  ? "bg-primary text-white"
                  : "border border-white/10 text-slate-300"
              }`}
              onClick={() => setRange(item as 5 | 7 | 10)}
              type="button"
            >
              {item}年
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {metricOptions.map((option) => (
          <button
            key={option.key}
            aria-label={`切换到${option.label}`}
            className={`rounded-full px-4 py-2 text-sm ${
              metric === option.key
                ? "bg-accent text-white"
                : "border border-white/10 text-slate-300"
            }`}
            onClick={() => setMetric(option.key)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={displayData}>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.15)" strokeDasharray="3 3" />
            <XAxis dataKey="year" stroke="#94A3B8" />
            <YAxis stroke="#94A3B8" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0F172A",
                border: "1px solid rgba(148, 163, 184, 0.25)",
                borderRadius: "16px"
              }}
            />
            <Line
              dataKey={metric}
              dot={{ r: 4 }}
              stroke="#2563EB"
              strokeWidth={3}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
