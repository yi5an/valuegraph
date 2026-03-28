import Link from "next/link";
import { BarChart3, PieChart, Star } from "lucide-react";

const items = [
  { href: "/", label: "价值推荐", icon: Star },
  { href: "/financial", label: "财报分析", icon: BarChart3 },
  { href: "/shareholders", label: "持股查询", icon: PieChart }
];

/**
 * Desktop sidebar navigation.
 */
export function Sidebar(): JSX.Element {
  return (
    <aside className="sticky top-20 hidden h-[calc(100vh-6rem)] w-64 shrink-0 rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel desktop:block">
      <div className="mb-6">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">工作台</p>
        <h2 className="mt-2 text-lg font-semibold text-white">ValueGraph</h2>
      </div>
      <nav className="space-y-2">
        {items.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
