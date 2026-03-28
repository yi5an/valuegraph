"use client";

import Link from "next/link";
import { Menu, TrendingUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "价值推荐" },
  { href: "/financial", label: "财报分析" },
  { href: "/shareholders", label: "持股查询" }
];

/**
 * Top navigation bar with responsive menu.
 */
export function Header(): JSX.Element {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed inset-x-0 top-0 z-50 h-16 border-b border-white/10 bg-slate-950/85 backdrop-blur">
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-4 tablet:px-6">
        <Link className="flex items-center gap-3" href="/">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/20 text-primary">
            <TrendingUp className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-[0.2em] text-slate-200">
              VALUEGRAPH
            </div>
            <div className="text-xs text-slate-400">价值投资分析平台</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 desktop:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          aria-label="切换移动端导航菜单"
          className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-slate-200 desktop:hidden"
          onClick={() => setOpen((value) => !value)}
          type="button"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      <div
        className={cn(
          "desktop:hidden",
          open ? "border-t border-white/10 bg-slate-950/95" : "hidden"
        )}
      >
        <nav className="mx-auto flex max-w-7xl flex-col px-4 py-3">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-xl px-3 py-3 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
