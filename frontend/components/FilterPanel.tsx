"use client";

import { StockFilters } from "@/lib/types";

interface FilterPanelProps {
  filters: StockFilters;
  onChange: (filters: StockFilters) => void;
}

/**
 * Market filter controls for ROE and debt ratio.
 */
export function FilterPanel({
  filters,
  onChange
}: FilterPanelProps): JSX.Element {
  return (
    <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-white">价值筛选器</p>
          <p className="mt-1 text-sm text-slate-400">按照盈利能力与杠杆水平筛选股票。</p>
        </div>
        <button
          aria-label="重置筛选条件"
          className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
          onClick={() => onChange({ roeMin: 15, debtMax: 50 })}
          type="button"
        >
          重置
        </button>
      </div>

      <div className="mt-6 grid gap-6 tablet:grid-cols-2">
        <label className="block">
          <div className="mb-3 flex items-center justify-between text-sm text-slate-300">
            <span>ROE 下限</span>
            <span>{filters.roeMin}%</span>
          </div>
          <input
            aria-label="ROE 下限"
            className="w-full accent-primary"
            max={50}
            min={0}
            onChange={(event) =>
              onChange({ ...filters, roeMin: Number(event.target.value) })
            }
            type="range"
            value={filters.roeMin}
          />
        </label>

        <label className="block">
          <div className="mb-3 flex items-center justify-between text-sm text-slate-300">
            <span>负债率上限</span>
            <span>{filters.debtMax}%</span>
          </div>
          <input
            aria-label="负债率上限"
            className="w-full accent-accent"
            max={100}
            min={0}
            onChange={(event) =>
              onChange({ ...filters, debtMax: Number(event.target.value) })
            }
            type="range"
            value={filters.debtMax}
          />
        </label>
      </div>
    </section>
  );
}
