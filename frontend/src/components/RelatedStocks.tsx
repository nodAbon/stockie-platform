import React, { useState, useEffect } from 'react';
import { GitBranch, AlertTriangle, Gem, BarChart2, Loader, TrendingUp } from 'lucide-react';

interface RelatedStock {
  ticker: string;
  name: string;
  relation: string;
  tag: string;
  pe: number;
  pb: number;
  margin: number;
  growth: number;
  current_price: number;
  target_price: number;
  upside_pct: number;
  currency: string;
  price_note: string;
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
  const [stocks, setStocks]             = useState<RelatedStock[]>([]);
  const [themeReason, setThemeReason]   = useState<string>('');
  const [loading, setLoading]           = useState<boolean>(true);
  const [error, setError]               = useState<string>('');

  useEffect(() => {
    const fetchRelated = async () => {
      setLoading(true);
      setError('');
      setStocks([]);
      setThemeReason('');
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
    if (score >= 70) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const gradeIcon = (grade_color: string) => {
    if (grade_color === 'emerald') return <Gem size={13} className="text-emerald-400" />;
    if (grade_color === 'amber')   return <BarChart2 size={13} className="text-amber-400" />;
    return <AlertTriangle size={13} className="text-red-400" />;
  };

  const formatPrice = (price: number, currency: string) => {
    if (!price || price === 0) return '—';
    if (currency === 'KRW') return `${price.toLocaleString('ko-KR')}원`;
    return `$${price.toLocaleString('en-US')}`;
  };


  return (
    <div className="mt-8 rounded-2xl border border-indigo-500/25 bg-gradient-to-br from-gray-900/70 to-indigo-950/15 shadow-[0_0_20px_rgba(99,102,241,0.06)] overflow-hidden">

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-b border-indigo-500/15 bg-indigo-950/20">
        <div className="flex items-center gap-2 mb-1">
          <GitBranch size={18} className="text-indigo-400" />
          <span className="text-sm font-bold text-indigo-300 uppercase tracking-wider">
            연관 저평가 수혜주 레이더
          </span>
        </div>
        <p className="text-xs text-gray-400 font-semibold leading-relaxed">
          <strong className="text-gray-200">{primaryName}</strong>의 호재 뉴스와 동일한 수혜를 받는
          저평가·고수익 종목을 AI가 자동 선별합니다.
        </p>
        {themeReason && (
          <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30">
            <TrendingUp size={11} className="text-indigo-300" />
            <span className="text-xs font-bold text-indigo-200">{themeReason} 동반 수혜주</span>
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col gap-4">

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center gap-2 py-8 text-indigo-400 text-sm font-bold">
            <Loader size={16} className="animate-spin" />
            호재 테마 분석 중...
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <p className="text-sm text-gray-500 text-center py-6">{error}</p>
        )}

        {/* Stock cards */}
        {!loading && stocks.map((stock, idx) => (
          <div
            key={stock.ticker}
            className="rounded-xl border border-gray-700/50 bg-gray-900/40 hover:bg-gray-900/70 hover:border-indigo-500/30 transition-all duration-200"
          >
            {/* ── Card header ─────────────────────────────────── */}
            <div className="flex justify-between items-start p-4 pb-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center flex-wrap gap-1.5 mb-1">
                  <span className="text-[10px] font-black text-gray-500 bg-gray-800 rounded px-1.5 py-0.5">
                    #{idx + 1}
                  </span>
                  <span className="text-base font-black text-white">{stock.name}</span>
                  <span className="text-[10px] font-mono text-gray-500 bg-gray-900 border border-gray-700 rounded px-1.5 py-0.5">
                    {stock.ticker}
                  </span>
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/25 text-indigo-300">
                    {stock.tag}
                  </span>
                </div>
                <p className="text-xs text-gray-500 leading-tight">
                  🔗 {stock.relation}
                </p>
              </div>

              {/* Grade badge */}
              <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-3">
                <span className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border font-bold ${
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

            {/* ── Price row ────────────────────────────────────── */}
            {(stock.current_price > 0) && (
              <div className="mx-4 mb-3 p-3 rounded-xl bg-gray-950/50 border border-gray-800/60 flex items-center justify-between gap-4">
                <div>
                  <p className="text-[9px] text-gray-600 font-bold mb-0.5">현재가</p>
                  <p className={`text-lg font-black numeric-font ${
                    stock.upside_pct > 0 ? 'text-emerald-400' : stock.upside_pct < 0 ? 'text-red-400' : 'text-white'
                  }`}>
                    {formatPrice(stock.current_price, stock.currency)}
                  </p>
                </div>
                <div className="flex items-center text-gray-600 font-bold text-lg">→</div>
                <div>
                  <p className="text-[9px] text-gray-600 font-bold mb-0.5">
                    목표가 <span className="text-gray-700">({stock.price_note})</span>
                  </p>
                  <p className="text-lg font-black text-white numeric-font">
                    {formatPrice(stock.target_price, stock.currency)}
                  </p>
                </div>
                {stock.upside_pct > 0 && (
                  <div className="ml-auto text-right">
                    <p className="text-[9px] text-gray-600 font-bold mb-0.5">예상 수익률</p>
                    <p className="text-base font-black text-white numeric-font">
                      +{stock.upside_pct}%
                    </p>
                  </div>
                )}
                {stock.upside_pct < 0 && (
                  <div className="ml-auto text-right">
                    <p className="text-[9px] text-gray-600 font-bold mb-0.5">예상 수익률</p>
                    <p className="text-base font-black text-white numeric-font">
                      {stock.upside_pct}%
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ── Metrics row ──────────────────────────────────── */}
            <div className="mx-4 mb-3 grid grid-cols-4 gap-2">
              {[
                {
                  label: 'PER',
                  sublabel: '낮을수록 저렴',
                  value: stock.pe > 0 ? stock.pe.toFixed(1) : 'N/A',
                  good: stock.pe > 0 && stock.pe < 20
                },
                {
                  label: 'PBR',
                  sublabel: '낮을수록 저평가',
                  value: stock.pb > 0 ? stock.pb.toFixed(2) : 'N/A',
                  good: stock.pb > 0 && stock.pb < 2
                },
                {
                  label: '이익률',
                  sublabel: '높을수록 우량',
                  value: stock.margin > 0 ? `${stock.margin}%` : 'N/A',
                  good: stock.margin >= 15
                },
                {
                  label: '매출성장',
                  sublabel: '높을수록 성장',
                  value: stock.growth !== 0 ? `${stock.growth > 0 ? '+' : ''}${stock.growth}%` : 'N/A',
                  good: stock.growth > 0
                },
              ].map(m => (
                <div key={m.label} className="bg-gray-950/50 rounded-lg p-2 text-center">
                  <p className="text-[9px] text-gray-500 font-bold leading-tight">{m.label}</p>
                  <p className="text-[8px] text-gray-700 leading-tight mb-1">{m.sublabel}</p>
                  <p className={`text-sm font-black numeric-font ${m.good ? 'text-emerald-400' : 'text-gray-400'}`}>
                    {m.value}
                  </p>
                </div>
              ))}
            </div>

            {/* ── Value score bar ──────────────────────────────── */}
            <div className="mx-4 mb-3">
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] text-gray-500 font-bold">
                  AI 종합 가치 점수
                  <span className="text-gray-600 ml-1">(저평가 + 수익성 + 성장성)</span>
                </span>
                <span className="text-sm font-black numeric-font" style={{ color: scoreBarColor(stock.value_score) }}>
                  {stock.value_score}/100
                </span>
              </div>
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${stock.value_score}%`, backgroundColor: scoreBarColor(stock.value_score) }}
                />
              </div>
            </div>

            {/* ── Highlights ───────────────────────────────────── */}
            <div className="px-4 pb-4 flex flex-wrap gap-1.5">
              {stock.highlights.map((h, i) => (
                <span key={i} className="text-[10px] px-2 py-1 rounded-lg bg-indigo-950/40 border border-indigo-500/15 text-indigo-300 font-semibold">
                  ✦ {h}
                </span>
              ))}
            </div>
          </div>
        ))}

        {/* Disclaimer */}
        {!loading && stocks.length > 0 && (
          <p className="text-[9px] text-gray-600 text-center border-t border-gray-800 pt-3 leading-relaxed">
            ⚠️ AI 종합 가치 점수는 PER·PBR·이익률·성장률 기반 참고 지표이며, 투자 권유가 아닙니다.
            현재가·목표가는 추정치로 실제와 다를 수 있습니다. 실제 투자 전 반드시 추가 조사를 하시기 바랍니다.
          </p>
        )}
      </div>
    </div>
  );
};
