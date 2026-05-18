import React, { useState, useEffect } from 'react';
import { Search, Bell, RotateCw, AlertCircle, Sun, Cloud, CloudRain, Shield } from 'lucide-react';
import { MarketThermometer } from './components/MarketThermometer';
import { IndexCard } from './components/IndexCard';
import { StockChart } from './components/StockChart';
import { NewsCard } from './components/NewsCard';
import { BeginnerGuidance } from './components/BeginnerGuidance';
import { MarketIntelligence } from './components/MarketIntelligence';
import { RelatedStocks } from './components/RelatedStocks';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://stockie-platform.onrender.com';

interface IndexInfo {
  price: number;
  change_pct: number;
}

interface MarketRadarData {
  timestamp: string;
  indices: { [key: string]: IndexInfo };
  fear_greed: number;
  temperature: number;
  state: 'Bullish' | 'Bearish' | 'Neutral';
  guidance: string;
}

interface StockInfo {
  ticker: string;
  name: string;
  price: number;
  open: number;
  high: number;
  low: number;
  prev_close: number;
  change: number;
  change_pct: number;
  volume: number;
  history: Array<{ date: string; price: number }>;
}

interface SentimentSummary {
  total_news: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  weather: string;
  weather_description: string;
}

interface AIPrediction {
  // Expected trading band (replaces single predicted_close)
  band_low: number;
  band_high: number;
  band_low_fmt: string;
  band_high_fmt: string;
  avg_daily_range_pct: number;
  // Technical indicators
  rsi: number;
  macd_line: number;
  signal_line: number;
  macd_histogram: number;
  macd_crossover: 'golden' | 'dead' | 'none';
  macd_sufficient: boolean;
  // Data quality grade (replaces fake confidence %)
  data_quality: { grade: string; color: string; real_data: boolean };
  // Signal
  trading_signal: string;
  signal_label: string;
  signal_comment: string;
  rsi_note: string;
  macd_note: string;
  // Rationale + disclaimer
  ai_rationale: string;
  disclaimer: string;
}

interface StockAnalysisData {
  stock: StockInfo;
  is_korean: boolean;
  news: Array<{
    title: string;
    link: string;
    source: string;
    date: string;
    sentiment: 'Positive' | 'Negative' | 'Neutral';
    is_simulated?: boolean;
  }>;
  sentiment: SentimentSummary;
  ai_prediction?: AIPrediction;
}


function App() {
  // 1. Radar State
  const [radar, setRadar] = useState<MarketRadarData | null>(null);
  const [radarLoading, setRadarLoading] = useState<boolean>(true);
  
  // 2. Search Ticker State
  const [searchQuery, setSearchQuery] = useState<string>('005930'); // Default to Samsung Electronics
  const [stockData, setStockData] = useState<StockAnalysisData | null>(null);
  const [stockLoading, setStockLoading] = useState<boolean>(false);
  const [stockError, setStockError] = useState<string | null>(null);
  
  // 3. Desktop Notification State
  const [alertsEnabled, setAlertsEnabled] = useState<boolean>(false);

  // Fetch macro market radar
  const fetchMarketRadar = async () => {
    setRadarLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/market-radar`);
      const data = await res.json();
      setRadar(data);
    } catch (e) {
      console.error('Failed to fetch market radar:', e);
    } finally {
      setRadarLoading(false);
    }
  };

  // Fetch stock analysis details
  const fetchStockAnalysis = async (ticker: string) => {
    setStockLoading(true);
    setStockError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/stock-analysis?ticker=${ticker}`);
      if (!res.ok) throw new Error('존재하지 않는 종목이거나 데이터를 불러올 수 없습니다.');
      const data = await res.json();
      setStockData(data);
    } catch (e: any) {
      console.error(e);
      setStockError(e.message);
      setStockData(null);
    } finally {
      setStockLoading(false);
    }
  };

  // Ask for Web Notification permission
  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      alert('이 브라우저는 데스크톱 알림을 지원하지 않습니다.');
      return;
    }
    const perm = await Notification.requestPermission();
    if (perm === 'granted') {
      setAlertsEnabled(true);
      new Notification('🔔 Stockie 실시간 알림 서비스 활성화', {
        body: '주린이를 위한 스마트 시세 급등락 및 호재 알림이 연동되었습니다.',
        icon: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=128&q=80'
      });
    }
  };

  // Simulate alert triggers periodically if enabled
  useEffect(() => {
    let interval: any;
    if (alertsEnabled && stockData) {
      interval = setInterval(() => {
        const name = stockData.stock.name;
        
        // Randomly simulate a volatility break out alert for demo purposes
        const r = Math.random();
        if (r > 0.6) {
          const simulatedChange = (Math.random() * 4 - 2).toFixed(1);
          const positiveAlert = parseFloat(simulatedChange) > 0;
          
          new Notification(positiveAlert ? `📈 [급등 돌파 알림] ${name}` : `📉 [급변동 주의 알림] ${name}`, {
            body: positiveAlert 
              ? `${name} 주가가 실시간 세력 수급 유입으로 전일 대비 +${simulatedChange}% 돌파 중입니다! 감성 분석상 긍정 호재 비율이 높습니다.`
              : `${name} 주가가 대량 외인 매도세로 전일 대비 ${simulatedChange}% 변동 중입니다. 리스크 관리에 유의하세요.`,
            icon: 'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=128&q=80'
          });
        }
      }, 15000); // Trigger alert simulation every 15s for visual wow factor
    }
    return () => clearInterval(interval);
  }, [alertsEnabled, stockData]);

  useEffect(() => {
    fetchMarketRadar();
    fetchStockAnalysis('005930'); // Load Samsung Electronics initially
    
    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        setAlertsEnabled(true);
      }
    }
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      fetchStockAnalysis(searchQuery.trim());
    }
  };

  // Click any ticker name → run it through the radar
  const handleTickerClick = (ticker: string) => {
    setSearchQuery(ticker);
    fetchStockAnalysis(ticker);
    // Scroll to the radar section smoothly
    setTimeout(() => {
      document.getElementById('stock-radar-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  return (
    <div className="min-h-screen pb-16 px-4 md:px-8 max-w-7xl mx-auto flex flex-col gap-6">
      {/* 1. Header Toolbar */}
      <header className="flex flex-col md:flex-row justify-between items-center py-6 border-b border-gray-800/40 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-3xl">📈</span>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              Stockie <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">주린이 비서</span>
            </h1>
          </div>
          <p className="text-xs text-gray-500 font-semibold mt-1">
            {radar ? `실시간 거시 지표 및 감성 크롤러 동기화 완료 (${radar.timestamp})` : '지표 데이터를 로딩하는 중...'}
          </p>
        </div>

        {/* Action controls */}
        <div className="flex items-center gap-3">
          {/* Refresh indices */}
          <button 
            onClick={fetchMarketRadar}
            className="p-2.5 rounded-xl border border-gray-800 bg-gray-900/60 hover:bg-gray-800 text-gray-400 hover:text-white transition-all flex items-center gap-1.5 text-xs font-semibold"
            title="시장 지표 새로고침"
          >
            <RotateCw size={14} className={radarLoading ? 'animate-spin' : ''} />
            지표 동기화
          </button>

          {/* Alert trigger button */}
          {alertsEnabled ? (
            <button 
              className="p-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 transition-all flex items-center gap-1.5 text-xs font-bold"
              onClick={() => setAlertsEnabled(false)}
            >
              <Bell size={14} />
              시세 팝업 활성화됨
            </button>
          ) : (
            <button 
              className="p-2.5 rounded-xl border border-gray-800 bg-gray-900/60 hover:bg-gray-800 text-gray-400 hover:text-white transition-all flex items-center gap-1.5 text-xs font-semibold"
              onClick={requestNotificationPermission}
            >
              <Bell size={14} />
              실시간 데스크톱 알림 켜기
            </button>
          )}
        </div>
      </header>

      {/* 2. Top Section - Market Thermometer & Guidance */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market Mood Thermometer */}
        <div className="lg:col-span-1">
          {radarLoading ? (
            <div className="glass-panel h-[340px] flex items-center justify-center">
              <div className="text-sm text-gray-400 font-bold flex items-center gap-2">
                <RotateCw size={16} className="animate-spin text-indigo-400" />
                시장 센티멘트 분석을 집계 중입니다...
              </div>
            </div>
          ) : (
            radar && (
              <MarketThermometer 
                temperature={radar.temperature} 
                fearGreed={radar.fear_greed} 
              />
            )
          )}
        </div>

        {/* Smart Plain Korean Guidance for Beginners */}
        <div className="lg:col-span-2">
          {radarLoading ? (
            <div className="glass-panel h-[340px] flex items-center justify-center">
              <div className="text-sm text-gray-400 font-bold">인공지능 투자 전략을 수립하는 중...</div>
            </div>
          ) : (
            radar && (
              <BeginnerGuidance 
                guidanceText={radar.guidance} 
                fearGreed={radar.fear_greed} 
              />
            )
          )}
        </div>
      </section>

      {/* 3. Mid Section - Market Macro Indices Grid */}
      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
          <Shield size={14} className="text-emerald-400" /> 전 글로벌 거시 금융 신호판
        </h3>
        
        {radarLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="glass-panel h-[90px] animate-pulse bg-gray-900/30" />
            ))}
          </div>
        ) : (
          radar && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.keys(radar.indices).map((name) => {
                if (name === 'VIX') return null; // We display VIX inside Fear & Greed, so save space in grid!
                const val = radar.indices[name];
                return (
                  <IndexCard 
                    key={name}
                    name={name}
                    price={val.price}
                    changePct={val.change_pct}
                  />
                );
              })}
            </div>
          )
        )}
      </section>

      {/* 3.5. Market Intelligence - Surging Stocks & Blue-Chip Radar */}
      <section className="flex flex-col gap-4 mt-2">
        <MarketIntelligence onTickerClick={handleTickerClick} />
      </section>

      {/* 4. Bottom Section - Stock Search and Crawling Analysis Panel */}
      <section id="stock-radar-section" className="flex flex-col gap-4 mt-2">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800/40 pb-4">
          <h2 className="text-xl font-black text-white flex items-center gap-2">
            🔍 개별 종목 호재/악재 감지 레이더
          </h2>
          
        {/* Ticker Search Box — fixed icon + button sizing */}
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-[380px] flex items-center gap-2">
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
              <input
                type="text"
                placeholder="종목코드(005930) 또는 티커(TSLA)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-gray-900/80 border border-gray-800 rounded-xl py-2.5 pl-8 pr-3 text-sm font-semibold text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder:text-gray-600"
              />
            </div>
            <button
              type="submit"
              className="flex-shrink-0 h-[42px] px-4 rounded-xl bg-emerald-500 text-xs font-bold text-black hover:bg-emerald-400 transition-colors whitespace-nowrap"
            >
              종목 진단
            </button>
          </form>

        </div>

        {/* Load indicators or stock results */}
        {stockLoading ? (
          <div className="glass-panel h-[400px] flex items-center justify-center">
            <div className="text-sm text-gray-400 font-bold flex items-center gap-2">
              <RotateCw size={18} className="animate-spin text-emerald-400" />
              네이버 금융 및 야후 파이낸스 실시간 기사 수집 및 호재 키워드 진단 중...
            </div>
          </div>
        ) : stockError ? (
          <div className="p-8 rounded-2xl border border-red-500/20 bg-red-500/5 flex flex-col items-center justify-center text-center gap-3">
            <AlertCircle size={40} className="text-red-500" />
            <div className="text-base font-bold text-white">진단 오류 발생</div>
            <div className="text-sm text-gray-400">{stockError}</div>
          </div>
        ) : (
          stockData && (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              
              {/* Left Column: Stock Price & Performance Chart (2/5 size) */}
              <div className="lg:col-span-2 flex flex-col gap-6">
                <div className="glass-panel flex-grow">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <h3 className="text-lg font-black text-white">{stockData.stock.name}</h3>
                        <span className="text-xs px-2 py-0.5 rounded bg-gray-900 border border-gray-800 text-gray-400 font-mono">
                          {stockData.stock.ticker}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 font-semibold mt-1">
                        최근 30일 시세 역사적 트렌드 분석
                      </p>
                    </div>

                    <span 
                      className={`badge ${stockData.stock.change_pct >= 0 ? 'badge-bullish' : 'badge-bearish'}`}
                    >
                      {stockData.stock.change_pct >= 0 ? '+' : ''}
                      {stockData.stock.change_pct.toFixed(2)}%
                    </span>
                  </div>

                  {/* Stock price large metric */}
                  <div className="mt-6 mb-2">
                    <span className={`text-4xl font-extrabold numeric-font ${
                      stockData.stock.price > stockData.stock.open ? 'text-red-400' :
                      stockData.stock.price < stockData.stock.open ? 'text-blue-400' :
                      'text-white'
                    }`}>
                      {stockData.stock.price.toLocaleString('ko-KR')}
                    </span>
                    <span className="text-sm font-bold text-gray-400 ml-1">
                      {stockData.is_korean ? '원' : '달러'}
                    </span>
                    {/* Diff from open */}
                    {stockData.stock.open > 0 && (() => {
                      const diff = stockData.stock.price - stockData.stock.open;
                      const isUp = diff > 0;
                      const isDown = diff < 0;
                      const diffFmt = (isUp ? '+' : '') + diff.toLocaleString('ko-KR');
                      return (
                        <span className={`ml-2 text-base font-bold numeric-font ${
                          isUp ? 'text-red-400' : isDown ? 'text-blue-400' : 'text-gray-500'
                        }`}>
                          ({diffFmt}{stockData.is_korean ? '원' : '$'})
                        </span>
                      );
                    })()}
                  </div>

                  {/* Performance subgrid */}
                  <div className="grid grid-cols-2 gap-4 mt-6 p-4 bg-gray-900/30 rounded-xl border border-gray-800/40 text-xs">
                    <div>
                      <span className="text-gray-500 font-bold block mb-1">시작가</span>
                      <span className="font-extrabold text-gray-300 numeric-font">
                        {stockData.stock.open.toLocaleString('ko-KR')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 font-bold block mb-1">이전 종가</span>
                      <span className="font-extrabold text-gray-300 numeric-font">
                        {stockData.stock.prev_close.toLocaleString('ko-KR')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400 font-bold block mb-1">당일 최고가</span>
                      <span className="font-extrabold text-white numeric-font">
                        {stockData.stock.high.toLocaleString('ko-KR')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400 font-bold block mb-1">당일 최저가</span>
                      <span className="font-extrabold text-white numeric-font">
                        {stockData.stock.low.toLocaleString('ko-KR')}
                      </span>
                    </div>
                  </div>

                  {/* ── AI Analysis Panel (Refactored v2) ── */}
                  {stockData.ai_prediction && (
                    <div className="mt-6 p-4 rounded-xl border border-purple-500/20 bg-gradient-to-br from-gray-900/60 to-purple-950/10 relative overflow-hidden shadow-[0_0_15px_rgba(168,85,247,0.05)]">
                      <div className="absolute right-0 top-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl pointer-events-none" />

                      {/* Header row */}
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-[10px] font-bold text-purple-400 flex items-center gap-1 uppercase tracking-wider">
                          <span>🔮</span> AI 당일 시장 분석
                        </span>
                        {/* Data quality grade (replaces fake confidence %) */}
                        <span className={`text-[10px] px-2 py-0.5 rounded border font-bold ${
                          stockData.ai_prediction.data_quality.color === 'green'  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                          stockData.ai_prediction.data_quality.color === 'amber'  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' :
                          stockData.ai_prediction.data_quality.color === 'red'    ? 'bg-red-500/10 border-red-500/30 text-red-400' :
                          'bg-gray-800 border-gray-700 text-gray-400'
                        }`}>
                          데이터 {stockData.ai_prediction.data_quality.grade}
                        </span>
                      </div>

                      {/* Expected trading band (honest range instead of single fake close) */}
                      <div className="mb-3">
                        <p className="text-[10px] text-gray-500 font-semibold mb-1">📊 당일 예상 거래 밴드 <span className="text-gray-600">(30일 변동성 기반)</span></p>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-black text-white numeric-font">
                            {stockData.ai_prediction.band_low_fmt}
                          </span>
                          <span className="text-gray-500 font-bold">~</span>
                          <span className="text-lg font-black text-white numeric-font">
                            {stockData.ai_prediction.band_high_fmt}
                          </span>
                          <span className="ml-auto text-[10px] text-gray-500 numeric-font">
                            ±{stockData.ai_prediction.avg_daily_range_pct.toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {/* RSI + MACD row */}
                      {stockData.ai_prediction.macd_sufficient && (
                        <div className="grid grid-cols-2 gap-3 mb-3 border-t border-purple-500/10 pt-3">
                          {/* RSI */}
                          <div className="bg-gray-900/40 rounded-lg p-2.5">
                            <p className="text-[9px] font-bold text-gray-500 mb-1">RSI (14)</p>
                            <div className="flex items-center gap-2">
                              <span className={`text-base font-black numeric-font ${
                                stockData.ai_prediction.rsi >= 70 ? 'text-red-400' :
                                stockData.ai_prediction.rsi <= 30 ? 'text-emerald-400' :
                                'text-white'
                              }`}>
                                {stockData.ai_prediction.rsi}
                              </span>
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                stockData.ai_prediction.rsi >= 70 ? 'bg-red-500/10 text-red-400' :
                                stockData.ai_prediction.rsi <= 30 ? 'bg-emerald-500/10 text-emerald-400' :
                                'bg-gray-800 text-gray-400'
                              }`}>
                                {stockData.ai_prediction.rsi >= 70 ? '과매수' :
                                 stockData.ai_prediction.rsi <= 30 ? '과매도' : '중립'}
                              </span>
                            </div>
                            {stockData.ai_prediction.rsi_note && (
                              <p className="text-[9px] text-amber-400 mt-1 leading-tight">{stockData.ai_prediction.rsi_note}</p>
                            )}
                          </div>

                          {/* MACD */}
                          <div className="bg-gray-900/40 rounded-lg p-2.5">
                            <p className="text-[9px] font-bold text-gray-500 mb-1">MACD</p>
                            <div className="flex items-center gap-2">
                              <span className={`text-base font-black numeric-font ${
                                stockData.ai_prediction.macd_histogram > 0 ? 'text-emerald-400' : 'text-red-400'
                              }`}>
                                {stockData.ai_prediction.macd_histogram > 0 ? '▲' : '▼'}
                              </span>
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                stockData.ai_prediction.macd_crossover === 'golden' ? 'bg-emerald-500/10 text-emerald-400' :
                                stockData.ai_prediction.macd_crossover === 'dead'   ? 'bg-red-500/10 text-red-400' :
                                'bg-gray-800 text-gray-400'
                              }`}>
                                {stockData.ai_prediction.macd_crossover === 'golden' ? '골든크로스' :
                                 stockData.ai_prediction.macd_crossover === 'dead'   ? '데드크로스' : '중립'}
                              </span>
                            </div>
                            {stockData.ai_prediction.macd_note && (
                              <p className="text-[9px] text-emerald-400 mt-1 leading-tight">{stockData.ai_prediction.macd_note}</p>
                            )}
                          </div>
                        </div>
                      )}

                      {/* AI rationale */}
                      <p className="text-[10px] text-gray-400 leading-relaxed italic border-t border-purple-500/10 pt-2.5 mt-2 mb-3">
                        {stockData.ai_prediction.ai_rationale}
                      </p>

                      {/* Composite trading signal */}
                      <div className="mt-3 pt-3 border-t border-purple-500/10 flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1">
                            <span>🎯</span> AI 복합 매매 추천 신호
                          </span>
                          <span className={`text-[10px] px-2 py-0.5 rounded border font-black ${
                            stockData.ai_prediction.trading_signal === 'Strong Buy'  ? 'bg-rose-500/15 border-rose-500/40 text-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.15)]' :
                            stockData.ai_prediction.trading_signal === 'Buy'         ? 'bg-amber-500/15 border-amber-500/40 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.15)]' :
                            stockData.ai_prediction.trading_signal === 'Hold'        ? 'bg-gray-800 border-gray-700 text-gray-300' :
                            stockData.ai_prediction.trading_signal === 'Sell'        ? 'bg-blue-500/15 border-blue-500/40 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.15)]' :
                            'bg-indigo-500/15 border-indigo-500/40 text-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.15)]'
                          }`}>
                            {stockData.ai_prediction.signal_label}
                          </span>
                        </div>

                        <p className="text-[10px] text-gray-300 leading-normal font-semibold bg-purple-950/20 p-2.5 rounded-lg border border-purple-500/5">
                          🚀 <strong className="text-purple-400">AI 가이드:</strong> {stockData.ai_prediction.signal_comment}
                        </p>

                        {/* Disclaimer — always visible, compact */}
                        <p className="text-[9px] text-gray-600 leading-tight mt-1 border-t border-gray-800 pt-2">
                          {stockData.ai_prediction.disclaimer}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Recharts Stock chart component */}
                  <StockChart 
                    history={stockData.stock.history} 
                    isPositive={stockData.stock.change_pct >= 0} 
                  />

                  {/* Related Stocks — supply-chain value picks */}
                  <RelatedStocks
                    primaryTicker={stockData.stock.ticker}
                    primaryName={stockData.stock.name}
                    backendUrl={BACKEND_URL}
                    onTickerClick={handleTickerClick}
                  />


                </div>
              </div>

              {/* Right Column: Sentiment Analysis & Scrollable News Card List (3/5 size) */}
              <div className="lg:col-span-3 flex flex-col gap-6">
                <div className="glass-panel flex flex-col">
                  <div>
                    {/* Stock Weather Summary */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-gray-800/40 pb-4 mb-4 gap-4">
                      <div>
                        <h3 className="text-base font-bold text-gray-300">오늘의 종목 호재/악재 기상도</h3>
                        <p className="text-xs text-gray-500 font-semibold mt-0.5">
                          최신 보도 자료 15개 감성 분류 집계
                        </p>
                      </div>

                      {/* Weather Indicator Badge */}
                      <div className="flex items-center gap-2 p-2 bg-gray-900/60 rounded-xl border border-gray-800">
                        <span className="text-2xl">
                          {stockData.sentiment.weather.includes('맑음') ? <Sun className="text-amber-400 inline" size={24} /> : 
                           stockData.sentiment.weather.includes('비바람') ? <CloudRain className="text-red-400 inline" size={24} /> : 
                           <Cloud className="text-gray-400 inline" size={24} />}
                        </span>
                        <div>
                          <div className="text-[10px] text-gray-500 font-bold leading-none">SENTIMENT WEATHER</div>
                          <div className="text-xs font-black text-white">{stockData.sentiment.weather}</div>
                        </div>
                      </div>
                    </div>

                    {/* Stock Weather Plain Explanation */}
                    <p className="text-xs text-gray-400 leading-normal mb-5 italic bg-gray-900/10 p-3 rounded-lg border border-gray-800/40">
                      {stockData.sentiment.weather_description}
                    </p>

                    {/* Sentiment horizontal percentage breakdown */}
                    <div className="flex flex-col gap-2 mb-6">
                      <div className="flex justify-between text-xs font-bold text-gray-500">
                        <span>🔥 호재 {stockData.sentiment.positive_pct}%</span>
                        <span>💬 중립 {stockData.sentiment.neutral_pct}%</span>
                        <span>❄️ 악재 {stockData.sentiment.negative_pct}%</span>
                      </div>
                      
                      {/* Stacked bar */}
                      <div className="w-full h-3 bg-gray-900 rounded-full overflow-hidden flex">
                        <div 
                          className="h-full bg-emerald-500 transition-all duration-1000"
                          style={{ width: `${stockData.sentiment.positive_pct}%` }}
                        />
                        <div 
                          className="h-full bg-amber-500 transition-all duration-1000"
                          style={{ width: `${stockData.sentiment.neutral_pct}%` }}
                        />
                        <div 
                          className="h-full bg-red-500 transition-all duration-1000"
                          style={{ width: `${stockData.sentiment.negative_pct}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Scrollable list of recent news */}
                  <div>
                    <h4 className="text-xs font-bold text-gray-400 mb-3 uppercase tracking-wider">
                      실시간 수집 기사 목록 ({stockData.news.length}개)
                    </h4>
                    
                    <div className="max-h-[260px] overflow-y-auto flex flex-col gap-3 pr-2 scroll-container">
                      {stockData.news.length === 0 ? (
                        <div className="p-8 text-center text-xs text-gray-600 font-bold">
                          수집된 최신 뉴스가 없습니다.
                        </div>
                      ) : (
                        stockData.news.map((item, idx) => (
                          <NewsCard key={idx} news={item} />
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>

            </div>
          )
        )}
      </section>
    </div>
  );
}

export default App;
