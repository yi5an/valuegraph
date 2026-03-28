import { ShareholderRow } from "@/lib/types";

interface ShareholderTableProps {
  rows: ShareholderRow[];
}

/**
 * Tabular display of top shareholders.
 */
export function ShareholderTable({ rows }: ShareholderTableProps): JSX.Element {
  return (
    <div className="overflow-hidden rounded-3xl border border-white/10 bg-card/80 shadow-panel">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-300">
            <tr>
              <th className="px-4 py-4">排名</th>
              <th className="px-4 py-4">股东名称</th>
              <th className="px-4 py-4">持股数</th>
              <th className="px-4 py-4">比例</th>
              <th className="px-4 py-4">变动</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.rank} className="border-t border-white/5 text-slate-200">
                <td className="px-4 py-4">{row.rank}</td>
                <td className="px-4 py-4">{row.name}</td>
                <td className="px-4 py-4">{row.shares}</td>
                <td className="px-4 py-4">{row.ratio}</td>
                <td className="px-4 py-4">{row.change}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
