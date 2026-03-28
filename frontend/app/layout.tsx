import type { Metadata } from "next";
import "@/styles/globals.css";
import { Header } from "@/components/Layout/Header";
import { Sidebar } from "@/components/Layout/Sidebar";
import { MobileNav } from "@/components/Layout/MobileNav";

export const metadata: Metadata = {
  title: "ValueGraph",
  description: "Value investing analytics dashboard"
};

/**
 * Root layout for the ValueGraph frontend.
 */
export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>): JSX.Element {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <Header />
        <div className="mx-auto flex max-w-7xl gap-6 px-4 pb-24 pt-20 tablet:px-6 desktop:pb-10">
          <Sidebar />
          <main className="min-w-0 flex-1">{children}</main>
        </div>
        <MobileNav />
      </body>
    </html>
  );
}
