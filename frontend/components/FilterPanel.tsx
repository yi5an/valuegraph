"use client";

import { useState } from "react";
import { StockFilters, SlidersHorizontal, ChevronDown } from "lucide-react";

interface AdvancedFilters extends StockFilters {
  grossMarginMin?: number;
  sortBy?: "score" | "roe" | "pe" | "market_cap";
}

interface FilterPanelProps {
  filters: AdvancedFilters;
  onChange: (filters: AdvancedFilters) => void;
}

const SORT_OPTIONS = [
  { value: "score", label: "评分" },
  { value: "roe", label: "ROE" },
  { value: "pe", label: "PE" },
  { value: "market_cap", label: "市值" }
];

/**
 * Market filter controls for ROE, debt ratio, and advanced filters.
 */
export function FilterPanel({
  filters,
  onChange
}: FilterPanelProps): JSX.Element {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleApplyFilters = () => {
    // 触发筛选，由于 useEffect 监听 filters 变化，会自动重新加载
    onChange({ ...filters });
  };

  return (
    <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-white">价值筛选器</p>
          <p className="mt-1 text-sm text-slate-400">按照盈利能力与杠杆水平筛选股票。</p>
        </div>
        <div className="flex gap-2">
          <button
            aria-label="显示高级筛选"
            className={`rounded-full border px-4 py-2 text-sm transition flex items-center gap-2 ${
              showAdvanced
                ? "border-primary bg-primary/15 text-primary"
                : "border-white/10 text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
            onClick={() => setShowAdvanced(!showAdvanced)}
            type="button"
          >
            <SlidersHorizontal className="h-4 w-4" />
            高级
          </button>
          <button
            aria-label="重置筛选条件"
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
            onClick={() => onChange({ roeMin: 15, debtMax: 50 })}
            type="button"
          >
            重置
          </button>
        </div>
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

      {/* 高级筛选面板 */}
      {showAdvanced && (
        <div className="mt-6 pt-6 border-t border-white/10">
          <p className="text-sm font-medium text-white mb-4">高级筛选</p>
          
          <div className="grid gap-6 tablet:grid-cols-3">
            {/* 毛利率最小值 */}
            <label className="block">
              <div className="mb-3 flex items-center justify-between text-sm text-slate-300">
                <span>毛利率下限</span>
                <span>{filters.grossMarginMin || 0}%</span>
              </div>
              <input
                aria-label="毛利率下限"
                className="w-full accent-positive"
                max={100}
                min={0}
                onChange={(event) =>
                  onChange({ ...filters, grossMarginMin: Number(event.target.value) })
                }
                type="range"
                value={filters.grossMarginMin || 0}
              />
            </label>

            {/* 排序字段 */}
            <label className="block">
              <div className="mb-3 text-sm text-slate-300">
                <span>排序方式</span>
              </div>
              <div className="relative">
                <select
                  aria-label="排序字段"
                  className="w-full appearance-none rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-sm text-white focus:border-primary focus:outline-none"
                  value={filters.sortBy || "score"}
                  onChange={(e) =>
                    onChange({ ...filters, sortBy: e.target.value as AdvancedFilters["sortBy"] })
                  }
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
              </div>
            </label>

            {/* 应用筛选按钮 */}
            <div className="flex items-end">
              <button
                onClick={handleApplyFilters}
                className="w-full rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white transition hover:bg-primary/90"
                type="button"
              >
                应用筛选
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
