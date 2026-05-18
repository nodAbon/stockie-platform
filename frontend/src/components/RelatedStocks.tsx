import React, { useState, useEffect } from 'react';
import { GitBranch, AlertTriangle, Gem, BarChart2, Loader } from 'lucide-react';

interface RelatedStock {
  ticker: string;
  name: string;
  relation: string;
  tag: string;
  pe: number;
  pb: number;
  margin: number;
  growth: number;
  value_score: number;
  value_grade: string;
  grade_color: string;
  highlights: string[];
  data_source: string;
}

interface RelatedStocksProps {
  primaryTicker: string;
  primaryName: string;
  backendUrl: string;
}

export const RelatedStocks: React.FC<RelatedStocksProps> = ({ primaryTicker, primaryName, backendUrl }) => {
  const [stocks, setStocks]       = useState<RelatedStock[]>([]);
  const [themeReason, setThemeReason] = useState<string>('');
  const [loading, setLoading]     = useState<boolean>(true);
  const [error, setError]         = useState<string>('');

  useEffect(() => {
    const fetchRelated = async () => {
      setLoading(true);
      setError('');
      setStocks([]);
      try {
        const res = await fetch(`${backendUrl}/api/related-stocks?ticker=${primaryTicker}`);
        if (!res.ok) throw new Error('API 응답 오류');
        const data = await res.json();
        if (data.related && data.related.length > 0) {
          setStocks(data.related);
          setThemeReason(data.theme_reason || '');
        } else {
          setError('이 종목의 뉴스에서 호재 테마를 감지할 수 없었습니다.');
        }
      } catch (e) {
        setError('연관 종목 데이터를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    fetchRelated();
  }, [primaryTicker, backendUrl]);

  const scoreBarColor = (score: number) => {
    if (score >= 70) return '#10b981'; // emerald
    if (score >= 50) return '#f59e0b'; // amber
    return '#ef4444';                  // red
  };

  const gradeIcon = (grade_color: string) => {
    if (grade_color === 'emerald') return <Gem size={11} className="text-emerald-400" />;
    if (grade_color === 'amber')   return <BarChart2 size={11} className="text-amber-400" />;
    return <AlertTriangle size={11} className="text-red-400" />;
  };

  return (
    <div className="mt-6 p-4 rounded-xl border border-indigo-500/20 bg-gradient-to-br from-gray-900/60 to-indigo-950/10 shadow-[0_0_15px_rgba(99,102,241,0.04)]">
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <GitBranch size={15} className="text-indigo-400" />
        <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
          연관 저평가 수혜주 레이더
        </span>
      </div>
      <p className="text-[10px] text-gray-500 font-semibold mb-1">
        <strong className="text-gray-400">{primaryName}</strong>의 호재 뉴스에서 감지된 테마와 동일한 수혜를 받는 저평가 종목을 추천합니다.
      </p>
      {themeReason && (
        <div className="mb-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20">
          <span className="text-[10px] font-bold text-indigo-300">{themeReason} 동반 수혜주</span>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center gap-2 py-6 text-indigo-400 text-xs font-bold">
          <Loader size={14} className="animate-spin" />
          연관 종목 가치 분석 중...
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <p className="text-xs text-gray-500 text-center py-4">{error}</p>
      )}

      {/* Stock cards */}
      {!loading && stocks.length > 0 && (
        <div className="flex flex-col gap-3">
          {stocks.map((stock, idx) => (
            <div
              key={stock.ticker}
              className="p-3 rounded-xl border border-gray-800/60 bg-gray-900/30 hover:bg-gray-900/50 hover:border-indigo-500/20 transition-all group"
            >
              {/* Top row */}
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="flex items-center gap-1.5 mb-0.5">
                    {/* Rank badge */}
                    <span className="text-[9px] font-black text-gray-600 bg-gray-800 rounded px-1">#{idx + 1}</span>
                    <span className="text-sm font-bold text-white">{stock.name}</span>
                    <span className="text-[10px] font-mono text-gray-500 px-1.5 py-0.5 rounded bg-gray-900 border border-gray-800">
                      {stock.ticker}
                    </span>
                    {/* Tag */}
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                      {stock.tag}
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-500 leading-tight">
                    🔗 {stock.relation}
                  </p>
                </div>

                {/* Value grade badge */}
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded border font-bold ${
                    stock.grade_color === 'emerald' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                    stock.grade_color === 'amber'   ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' :
                    'bg-red-500/10 border-red-500/30 text-red-400'
                  }`}>
                    {gradeIcon(stock.grade_color)}
                    {stock.value_grade}
                  </span>
                  {stock.data_source === 'curated' && (
                    <span className="text-[8px] text-gray-600 font-bold">큐레이션 데이터</span>
                  )}
                </div>
              </div>

              {/* Metrics row */}
              <div className="grid grid-cols-4 gap-1.5 mb-2">
                {[
                  { label: 'PER', value: stock.pe > 0 ? stock.pe.toFixed(1) : 'N/A', good: stock.pe > 0 && stock.pe < 20 },
                  { label: 'PBR', value: stock.pb > 0 ? stock.pb.toFixed(2) : 'N/A', good: stock.pb > 0 && stock.pb < 2 },
                  { label: '이익률', value: stock.margin > 0 ? `${stock.margin}%` : 'N/A', good: stock.margin >= 15 },
                  { label: '매출성장', value: stock.growth !== 0 ? `${stock.growth > 0 ? '+' : ''}${stock.growth}%` : 'N/A', good: stock.growth > 0 },
                ].map(m => (
                  <div key={m.label} className="bg-gray-950/40 rounded-lg p-1.5 text-center">
                    <p className="text-[8px] text-gray-600 font-bold mb-0.5">{m.label}</p>
                    <p className={`text-[10px] font-black ${m.good ? 'text-emerald-400' : 'text-gray-300'}`}>
                      {m.value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Value score bar */}
              <div className="mb-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[9px] text-gray-600 font-bold">가치 점수</span>
                  <span className="text-[10px] font-black" style={{ color: scoreBarColor(stock.value_score) }}>
                    {stock.value_score}/100
                  </span>
                </div>
                <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${stock.value_score}%`,
                      backgroundColor: scoreBarColor(stock.value_score)
                    }}
                  />
                </div>
              </div>

              {/* Highlights */}
              <div className="flex flex-wrap gap-1">
                {stock.highlights.map((h, i) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-950/30 border border-indigo-500/10 text-indigo-300 font-semibold">
                    ✦ {h}
                  </span>
                ))}
              </div>
            </div>
          ))}

          {/* Disclaimer */}
          <p className="text-[9px] text-gray-600 text-center mt-1 border-t border-gray-800 pt-2">
            ⚠️ 가치 점수는 PER·PBR·이익률·성장률 기반 참고 지표이며, 투자 권유가 아닙니다. 실제 투자 전 반드시 추가 조사를 하시기 바랍니다.
          </p>
        </div>
      )}
    </div>
  );
};
