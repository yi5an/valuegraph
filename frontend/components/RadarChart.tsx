"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer
} from "recharts";
import { FinancialHealthPoint } from "@/lib/types";

interface RadarChartProps {
  data: FinancialHealthPoint[];
}

/**
 * Financial health radar visualization.
 */
export function RadarChart({ data }: RadarChartProps): JSX.Element {
  return (
    <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
      <div>
        <p className="text-lg font-semibold text-white">财务健康度</p>
        <p className="mt-1 text-sm text-slate-400">从六个维度衡量企业经营质量。</p>
      </div>

      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsRadarChart data={data}>
            <PolarGrid stroke="rgba(148, 163, 184, 0.2)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: "#CBD5E1", fontSize: 12 }} />
            <Radar
              dataKey="score"
              fill="#F97316"
              fillOpacity={0.35}
              stroke="#F97316"
              strokeWidth={2}
            />
          </RechartsRadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
