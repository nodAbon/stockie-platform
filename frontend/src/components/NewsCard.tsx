import React from 'react';
import { ExternalLink } from 'lucide-react';

interface NewsItem {
  title: string;
  link: string;
  source: string;
  date: string;
  sentiment: 'Positive' | 'Negative' | 'Neutral';
  is_simulated?: boolean;
}

interface NewsCardProps {
  news: NewsItem;
}

export const NewsCard: React.FC<NewsCardProps> = ({ news }) => {
  let badgeClass = 'badge-neutral';
  let badgeLabel = '💬 중립';
  let borderGlow = 'rgba(255, 255, 255, 0.05)';

  if (news.sentiment === 'Positive') {
    badgeClass = 'badge-bullish';
    badgeLabel = '🔥 호재';
    borderGlow = 'rgba(0, 230, 118, 0.05)';
  } else if (news.sentiment === 'Negative') {
    badgeClass = 'badge-bearish';
    badgeLabel = '❄️ 악재';
    borderGlow = 'rgba(255, 23, 68, 0.05)';
  }

  return (
    <div
      className="p-4 rounded-xl border transition-all duration-300 hover:bg-white/[0.01]"
      style={{
        backgroundColor: 'rgba(20, 26, 38, 0.25)',
        borderColor: 'rgba(255, 255, 255, 0.05)',
        boxShadow: `0 0 10px ${borderGlow}`,
        opacity: news.is_simulated ? 0.7 : 1
      }}
    >
      <div className="flex justify-between items-start gap-4 mb-3">
        <a
          href={news.link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-semibold text-gray-200 hover:text-white leading-relaxed flex items-center gap-1 group"
        >
          <span className="group-hover:underline">{news.title}</span>
          <ExternalLink size={12} className="inline opacity-40 group-hover:opacity-100 transition-opacity flex-shrink-0" />
        </a>
      </div>

      <div className="flex justify-between items-center text-xs">
        <div className="flex items-center gap-2 text-gray-500">
          <span className="font-bold text-gray-400">{news.source}</span>
          <span>•</span>
          <span>{news.date}</span>
          {/* Simulation badge */}
          {news.is_simulated && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-500 font-bold">
              ⚠️ 시뮬레이션
            </span>
          )}
        </div>

        <span className={`badge ${badgeClass}`}>
          {badgeLabel}
        </span>
      </div>
    </div>
  );
};
