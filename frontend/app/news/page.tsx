"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus, Link2 } from "lucide-react";
import { getHotNews, getStockNews } from "@/lib/api";
import { NewsItem } from "@/lib/types";

interface RelatedNewsItem extends NewsItem {
  related_entities?: string[];
  relevance_score?: number;
}

// 情感标签组件
function SentimentTag({ sentiment }: { sentiment?: "positive" | "negative" | "neutral" }) {
  if (!sentiment) return null;
  
  const config = {
    positive: { icon: TrendingUp, label: "正面", className: "bg-green-500/20 text-green-400" },
    negative: { icon: TrendingDown, label: "负面", className: "bg-red-500/20 text-red-400" },
    neutral: { icon: Minus, label: "中性", className: "bg-slate-500/20 text-slate-400" }
  };
  
  const { icon: Icon, label, className } = config[sentiment];
  
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${className}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

/**
 * News page showing hot news and stock-related news.
 */
export default function NewsPage(): JSX.Element {
  const [hotNews, setHotNews] = useState<NewsItem[]>([]);
  const [stockNews, setStockNews] = useState<NewsItem[]>([]);
  const [relatedNews, setRelatedNews] = useState<RelatedNewsItem[]>([]);
  const [stockCode, setStockCode] = useState("");
  const [searchCode, setSearchCode] = useState("");
  const [loadingHot, setLoadingHot] = useState(true);
  const [loadingStock, setLoadingStock] = useState(false);
  const [loadingRelated, setLoadingRelated] = useState(false);
  const [errorHot, setErrorHot] = useState<string | null>(null);
  const [errorStock, setErrorStock] = useState<string | null>(null);
  const [errorRelated, setErrorRelated] = useState<string | null>(null);

  // Load hot news on mount
  useEffect(() => {
    let active = true;
    setLoadingHot(true);
    setErrorHot(null);

    getHotNews()
      .then((result) => {
        if (!active) return;
        if (result) {
          setHotNews(result);
        } else {
          setErrorHot("热点新闻加载失败");
        }
      })
      .catch(() => {
        if (!active) return;
        setErrorHot("热点新闻加载失败");
      })
      .finally(() => {
        if (active) {
          setLoadingHot(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  // Load stock news when search is triggered
  useEffect(() => {
    if (!searchCode) return;

    let active = true;
    setLoadingStock(true);
    setErrorStock(null);

    getStockNews(searchCode)
      .then((result) => {
        if (!active) return;
        if (result) {
          setStockNews(result);
        } else {
          setErrorStock("未找到相关新闻");
        }
      })
      .catch(() => {
        if (!active) return;
        setErrorStock("新闻加载失败");
      })
      .finally(() => {
        if (active) {
          setLoadingStock(false);
        }
      });

    // 同时加载关联新闻
    setLoadingRelated(true);
    setErrorRelated(null);
    
    fetch(`/api/news/related/${searchCode}`)
      .then(res => res.json())
      .then((result) => {
        if (!active) return;
        if (result.success && result.data) {
          setRelatedNews(result.data);
        } else {
          setRelatedNews([]);
        }
      })
      .catch(() => {
        if (!active) return;
        setErrorRelated("关联新闻加载失败");
      })
      .finally(() => {
        if (active) {
          setLoadingRelated(false);
        }
      });

    return () => {
      active = false;
    };
  }, [searchCode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (stockCode.trim()) {
      setSearchCode(stockCode.trim());
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) {
      return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours}小时前`;
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString("zh-CN");
    }
  };

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/10 bg-hero-grid bg-slate-900/70 p-6 shadow-panel tablet:p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-primary">News & Insights</p>
        <h1 className="mt-3 max-w-2xl text-3xl font-semibold text-white tablet:text-5xl">
          新闻资讯
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 tablet:text-base">
          实时追踪市场热点与个股新闻，把握投资机会
        </p>
      </section>

      {/* Stock Search */}
      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <h2 className="mb-4 text-lg font-semibold text-white">股票新闻查询</h2>
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value)}
            placeholder="输入股票代码（如 600519）"
            className="flex-1 rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-sm text-white placeholder-slate-500 focus:border-primary focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-xl bg-primary px-6 py-2 text-sm font-medium text-white transition hover:bg-primary/90"
          >
            搜索
          </button>
        </form>

        {/* Stock News Results */}
        {loadingStock && (
          <div className="mt-5 text-sm text-slate-300">加载中...</div>
        )}
        {errorStock && (
          <div className="mt-5 rounded-xl border border-negative/30 bg-negative/10 p-4 text-sm text-negative">
            {errorStock}
          </div>
        )}
        {!loadingStock && !errorStock && stockNews.length > 0 && (
          <div className="mt-5 space-y-3">
            {stockNews.map((item) => (
              <a
                key={item.id}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-xl border border-white/10 bg-slate-900/50 p-4 transition hover:border-primary/50 hover:bg-slate-900"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-medium text-white flex-1">{item.title}</h3>
                  {"sentiment" in item && (item as any).sentiment && (
                    <SentimentTag sentiment={(item as any).sentiment} />
                  )}
                </div>
                <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{formatTime(item.published_at)}</span>
                  {item.keywords && (
                    <>
                      <span>•</span>
                      <span className="text-primary">{item.keywords}</span>
                    </>
                  )}
                </div>
              </a>
            ))}
          </div>
        )}

        {/* 关联新闻分析 */}
        {searchCode && (
          <div className="mt-6 pt-6 border-t border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <Link2 className="h-5 w-5 text-indigo-400" />
              <h3 className="text-md font-semibold text-white">关联新闻分析</h3>
            </div>
            
            {loadingRelated && (
              <div className="text-sm text-slate-300">加载关联新闻中...</div>
            )}
            {errorRelated && (
              <div className="rounded-xl border border-negative/30 bg-negative/10 p-4 text-sm text-negative">
                {errorRelated}
              </div>
            )}
            {!loadingRelated && !errorRelated && relatedNews.length > 0 && (
              <div className="space-y-3">
                {relatedNews.map((item, idx) => (
                  <a
                    key={`related-${item.id}-${idx}`}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4 transition hover:border-indigo-500/40 hover:bg-indigo-500/10"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="text-sm font-medium text-white flex-1">{item.title}</h4>
                      {item.relevance_score !== undefined && (
                        <span className="text-xs text-indigo-400 bg-indigo-500/20 px-2 py-1 rounded">
                          相关度 {(item.relevance_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                      <span>{item.source}</span>
                      <span>•</span>
                      <span>{formatTime(item.published_at)}</span>
                      {item.related_entities && item.related_entities.length > 0 && (
                        <>
                          <span>•</span>
                          <div className="flex gap-1 flex-wrap">
                            {item.related_entities.slice(0, 3).map((entity, i) => (
                              <span key={i} className="text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                                {entity}
                              </span>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            )}
            {!loadingRelated && !errorRelated && relatedNews.length === 0 && (
              <div className="text-sm text-slate-400">暂无关联新闻</div>
            )}
          </div>
        )}
      </section>

      {/* Hot News */}
      <section className="rounded-3xl border border-white/10 bg-card/80 p-5 shadow-panel">
        <h2 className="mb-4 text-lg font-semibold text-white">热点新闻</h2>
        
        {loadingHot && (
          <div className="text-sm text-slate-300">加载中...</div>
        )}
        {errorHot && (
          <div className="rounded-xl border border-negative/30 bg-negative/10 p-4 text-sm text-negative">
            {errorHot}
          </div>
        )}
        {!loadingHot && !errorHot && hotNews.length > 0 && (
          <div className="space-y-3">
            {hotNews.map((item) => (
              <a
                key={item.id}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-xl border border-white/10 bg-slate-900/50 p-4 transition hover:border-primary/50 hover:bg-slate-900"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-medium text-white flex-1">{item.title}</h3>
                  {"sentiment" in item && (item as any).sentiment && (
                    <SentimentTag sentiment={(item as any).sentiment} />
                  )}
                </div>
                <p className="mt-2 text-xs text-slate-400 line-clamp-2">
                  {item.content}
                </p>
                <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{formatTime(item.published_at)}</span>
                  {item.keywords && (
                    <>
                      <span>•</span>
                      <span className="text-primary">{item.keywords}</span>
                    </>
                  )}
                </div>
              </a>
            ))}
          </div>
        )}
        {!loadingHot && !errorHot && hotNews.length === 0 && (
          <div className="text-sm text-slate-300">暂无热点新闻</div>
        )}
      </section>
    </div>
  );
}
