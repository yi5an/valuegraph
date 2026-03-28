"use client";

/**
 * Global error boundary UI.
 */
export default function Error({
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): JSX.Element {
  return (
    <div className="rounded-3xl border border-negative/30 bg-negative/10 p-8 shadow-panel">
      <p className="text-lg font-semibold text-negative">页面加载失败</p>
      <p className="mt-2 text-sm text-slate-200">请重试，或检查后端接口与本地依赖是否可用。</p>
      <button
        aria-label="重新加载页面"
        className="mt-5 rounded-full bg-negative px-4 py-2 text-sm font-medium text-white"
        onClick={() => reset()}
        type="button"
      >
        重试
      </button>
    </div>
  );
}
