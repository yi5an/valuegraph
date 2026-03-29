import Link from "next/link";
import { BarChart3, PieChart, Star, GitCompare, Network, Newspaper } from "lucide-react";

const items = [
  { href: "/", label: "推荐", icon: Star },
  { href: "/compare", label: "对比", icon: GitCompare },
  { href: "/financial", label: "财报", icon: BarChart3 },
  { href: "/shareholders", label: "持股", icon: PieChart }
];

/**
 * Bottom navigation shown on mobile screens.
 */
export function MobileNav(): JSX.Element {
  return (
    <nav className="fixed inset-x-4 bottom-4 z-50 rounded-3xl border border-white/10 bg-slate-900/90 p-2 shadow-panel backdrop-blur desktop:hidden">
      <ul className="grid grid-cols-4 gap-2">
        {items.map(({ href, label, icon: Icon }) => (
          <li key={href}>
            <Link
              aria-label={label}
              className="flex flex-col items-center justify-center rounded-2xl px-3 py-2 text-xs text-slate-300 transition hover:bg-white/5 hover:text-white"
              href={href}
            >
              <Icon className="mb-1 h-4 w-4" />
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
