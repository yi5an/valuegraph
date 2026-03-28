"use client";

import { useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { ShareholderTable } from "@/components/ShareholderTable";
import { mockData } from "@/lib/mockData";
import { ShareholderRecord } from "@/lib/types";

const colors = ["#2563EB", "#F97316", "#10B981", "#EF4444"];
const colorSwatches = ["bg-primary", "bg-accent", "bg-positive", "bg-negative"];

/**
 * Client shareholder lookup page.
 */
export function ClientShareholdersPage({
  initialData
}: {
  initialData: ShareholderRecord;
}): JSX.Element {
  const [current, setCurrent] = useState<ShareholderRecord>(initialData);

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-primary">Ownership Insight</p>
        <h1 className="mt-3 text-3xl font-semibold text-white tablet:text-4xl">
          股东结构、十大股东与机构持仓一站式查看
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          本分析基于价值投资，不构成买卖推荐。持股结构展示当前使用 mock 数据进行界面验证。
        </p>
      </section>

      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <div className="flex flex-wrap gap-2">
          {Object.values(mockData.shareholders).map((item) => (
            <button
              key={item.code}
              aria-label={`查看${item.company}股东信息`}
              className={`rounded-full border px-4 py-2 text-sm ${
                current.code === item.code
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-white/10 text-slate-300"
              }`}
              onClick={() => setCurrent(item)}
              type="button"
            >
              {item.company}
            </button>
          ))}
        </div>
      </section>

      <div className="grid gap-6 desktop:grid-cols-[1.2fr_1fr]">
        <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
          <p className="text-lg font-semibold text-white">股东结构饼图</p>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  cx="50%"
                  cy="50%"
                  data={current.ownership}
                  dataKey="value"
                  innerRadius={72}
                  outerRadius={110}
                  paddingAngle={3}
                >
                  {current.ownership.map((entry, index) => (
                    <Cell key={entry.name} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0F172A",
                    border: "1px solid rgba(148, 163, 184, 0.25)",
                    borderRadius: "16px"
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            {current.ownership.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-2 text-sm text-slate-300">
                <span className={`h-3 w-3 rounded-full ${colorSwatches[index % colorSwatches.length]}`} />
                {entry.name} {entry.value}%
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
          <p className="text-lg font-semibold text-white">机构持仓列表</p>
          <div className="mt-5 space-y-4">
            {current.institutions.map((institution) => (
              <article key={institution.institution} className="rounded-2xl bg-white/5 p-4">
                <p className="font-medium text-white">{institution.institution}</p>
                <p className="mt-2 text-sm text-slate-400">
                  持仓 {institution.position} · 占比 {institution.ratio}
                </p>
                <p className="mt-2 text-sm text-primary">{institution.action}</p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <section>
        <p className="mb-4 text-lg font-semibold text-white">十大股东</p>
        <ShareholderTable rows={current.topHolders} />
      </section>
    </div>
  );
}
