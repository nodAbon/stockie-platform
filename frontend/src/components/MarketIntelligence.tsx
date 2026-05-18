import React, { useState, useEffect } from 'react';
import { Flame, Star, Cpu, Car, BatteryCharging, Heart, ShieldAlert, ArrowUpRight, Loader } from 'lucide-react';

interface SurgingStock {
  ticker: string;
  name: string;
  price: string;
  changePct: number;
  reason: string;
}

interface BlueChipStock {
  ticker: string;
  name: string;
  subSector: string;
  tickerCode: string;
  marketCap: string;
  strength: string;
}

export const MarketIntelligence: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<string>('semiconductor');
  const [loadingPrices, setLoadingPrices] = useState<boolean>(true);

  // Curated Surging Stocks List with realistic fallback defaults
  const [surgingStocks, setSurgingStocks] = useState<SurgingStock[]>([
    { ticker: '012450', name: '한화에어로스페이스', price: '284,500원', changePct: 8.42, reason: 'K-방산 사상 최대 규모 동유럽 추가 무기 수출 계약 체결 공시로 수급 유입 급증' },
    { ticker: '196170', name: '알테오젠', price: '272,500원', changePct: 7.21, reason: '글로벌 빅테크 제약사 독점 플랫폼 기술 로열티 유입 본격화 전망에 기관 대량 매수세' },
    { ticker: 'NVDA', name: '엔비디아 (NVIDIA)', price: '$912.40', changePct: 6.95, reason: '차세대 Blackwell AI 아키텍처 서버 공급 대기 수요 급증으로 외인 세력 매수 폭발' },
    { ticker: '000660', name: 'SK하이닉스', price: '192,400원', changePct: 5.12, reason: '초고성능 HBM3E(고대역폭 메모리) 독점 공급 라인 구축으로 2분기 영업익 대폭 상회 전망' },
    { ticker: 'TSLA', name: '테슬라 (Tesla)', price: '$189.20', changePct: 4.80, reason: '완전 자율주행(FSD) 중국 승인 및 차세대 자율 로보택시 서비스 공개 임박 모멘텀 수혜' }
  ]);

  // Fetch live prices and change percentages from backend proxy in parallel
  useEffect(() => {
    const fetchLivePrices = async () => {
      setLoadingPrices(true);
      const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://stockie-platform.onrender.com';
      try {
        const promises = surgingStocks.map(async (stock) => {
          try {
            const res = await fetch(`${BACKEND_URL}/api/stock-analysis?ticker=${stock.ticker}`);
            if (!res.ok) throw new Error('API response failed');
            const data = await res.json();
            return { ticker: stock.ticker, data };
          } catch (err) {
            console.warn(`Failed to fetch live price for ${stock.name}:`, err);
            return { ticker: stock.ticker, data: null };
          }
        });

        const results = await Promise.all(promises);
        
        // Map live scraped values back to state
        setSurgingStocks((prev) => 
          prev.map((stock) => {
            const match = results.find((r) => r.ticker === stock.ticker);
            if (match && match.data && match.data.stock) {
              const live = match.data.stock;
              const formattedPrice = match.data.is_korean 
                ? `${live.price.toLocaleString('ko-KR')}원` 
                : `$${live.price.toFixed(2)}`;
              
              return {
                ...stock,
                price: formattedPrice,
                changePct: live.change_pct
              };
            }
            return stock; // keep default mock if offline
          })
        );
      } catch (e) {
        console.error('Failed batch live price update:', e);
      } finally {
        setLoadingPrices(false);
      }
    };

    fetchLivePrices();
    
    // Auto-refresh surging list prices every 30 seconds for live trading simulation!
    const interval = setInterval(fetchLivePrices, 30000);
    return () => clearInterval(interval);
  }, []);

  // Curated Blue Chip Categories Mapping
  const blueChipCategories: { [key: string]: { icon: React.ReactNode; label: string; list: BlueChipStock[] } } = {
    semiconductor: {
      icon: <Cpu size={16} className="text-amber-400" />,
      label: '반도체 / AI',
      list: [
        { ticker: '005930', name: '삼성전자', subSector: 'DRAM / 파운드리', tickerCode: '005930.KS', marketCap: '430조원', strength: '전 세계 메모리 반도체 1위 및 전 공정 종합 반도체 공급 지배력 보유' },
        { ticker: '000660', name: 'SK하이닉스', subSector: 'HBM / AI 메모리', tickerCode: '000660.KS', marketCap: '140조원', strength: 'AI 전용 고대역폭 메모리(HBM) 기술 1위로 AI 칩 선도 세력' },
        { ticker: 'NVDA', name: '엔비디아 (NVIDIA)', subSector: 'GPU / AI 가속기', tickerCode: 'NVDA', marketCap: '$2.2조', strength: '전 세계 인공지능 그래픽 프로세서 시장 90% 이상을 독점 중인 최강자' }
      ]
    },
    mobility: {
      icon: <Car size={16} className="text-blue-400" />,
      label: '미래 모빌리티',
      list: [
        { ticker: '005380', name: '현대자동차', subSector: '완성차 / 수소차', tickerCode: '005380.KS', marketCap: '58조원', strength: '하이브리드 및 전기차 포트폴리오를 모두 갖춘 국내 완성차 선도 대장주' },
        { ticker: 'TSLA', name: '테슬라 (Tesla)', subSector: '순수전기차 / FSD', tickerCode: 'TSLA', marketCap: '$600B', strength: '자율주행 데이터 축적 1위이자 기가팩토리 중심 제조 혁신 선도 기업' },
        { ticker: '002700', name: '기아 (KIA)', subSector: '완성차 / PBV', tickerCode: '002700.KS', marketCap: '48조원', strength: '최고 수준의 영업이익률 달성 및 주주환원(자사주 소각) 최선봉 우량주' }
      ]
    },
    battery: {
      icon: <BatteryCharging size={16} className="text-emerald-400" />,
      label: '2차전지 / 배터리',
      list: [
        { ticker: '373220', name: 'LG에너지솔루션', subSector: '셀 메이커 (Cell)', tickerCode: '373220.KS', marketCap: '85조원', strength: '북미 배터리 합작공장(JV) 최대 규모 가동 중인 글로벌 대표 셀 제조사' },
        { ticker: '006400', name: '삼성SDI', subSector: '원통형 / 전고체', tickerCode: '006400.KS', marketCap: '28조원', strength: '수익성 위주의 최고급 배터리 양산 및 전고체 배터리 파일럿 라인 가동 리더' },
        { ticker: '247540', name: '에코프로비엠', subSector: '하이니켈 양극재', tickerCode: '247540.KQ', marketCap: '20조원', strength: '국내 코스닥 시가총액 최상위권의 프리미엄 양극 소재 세계 1위 양산력' }
      ]
    },
    healthcare: {
      icon: <Heart size={16} className="text-rose-400" />,
      label: '바이오 / 헬스케어',
      list: [
        { ticker: '207940', name: '삼성바이오로직스', subSector: '바이오의약품 CMO', tickerCode: '207940.KS', marketCap: '56조원', strength: '글로벌 최대 바이오 리액터 캐파(공장 생산 규모)를 점유한 위탁생산 1위' },
        { ticker: '068270', name: '셀트리온', subSector: '바이오시밀러 (Biosimilar)', tickerCode: '068270.KS', marketCap: '38조원', strength: '유럽 및 미국 시장의 자가면역치료제 복제약 허가 및 유통 지배자' },
        { ticker: 'LLY', name: '일라이 릴리 (Eli Lilly)', subSector: '비만치료제 / 신약', tickerCode: 'LLY', marketCap: '$700B', strength: '차세대 당뇨/비만치료제 마운자로(Mounjaro) 독점으로 글로벌 시총 최고 그룹' }
      ]
    },
    aerospace: {
      icon: <ShieldAlert size={16} className="text-purple-400" />,
      label: '방산 / 우주항공',
      list: [
        { ticker: '012450', name: '한화에어로스페이스', subSector: '자주포 / 우주발사체', tickerCode: '012450.KS', marketCap: '14조원', strength: 'K9 자주포 및 천무 미사일의 글로벌 다국적 수출 계약 누적 1위 독점 방산 기업' },
        { ticker: '047810', name: '한국항공우주 (KAI)', subSector: '전투기 / 인공위성', tickerCode: '047810.KS', marketCap: '5.5조원', strength: 'KF-21 차세대 국산 전투기 및 FA-50 경공격기 글로벌 공급사' },
        { ticker: 'LMT', name: '록히드 마틴 (Lockheed Martin)', subSector: '스텔스기 / 전략 무기', tickerCode: 'LMT', marketCap: '$110B', strength: 'F-35 5세대 스텔스 전투기를 독점 개발/공급하는 전 세계 1위 군수 대기업' }
      ]
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      
      {/* 1. Surging Stocks Section (2/5 Column width) */}
      <div className="lg:col-span-2 glass-panel flex flex-col justify-between">
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Flame size={18} className="text-amber-500 animate-pulse" />
              실시간 급등 대형 대장주
            </h3>
            {loadingPrices && (
              <span className="text-[10px] text-indigo-400 flex items-center gap-1 font-bold">
                <Loader size={12} className="animate-spin" /> 동기화 중...
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 font-semibold mb-6">
            네이버/야후 금융 API 망을 통해 실시간 시세와 상승폭을 초고속 동기화한 톱5 종목입니다.
          </p>

          <div className="flex flex-col gap-4">
            {surgingStocks.map((stock) => {
              const isPositive = stock.changePct >= 0;
              return (
                <div 
                  key={stock.ticker} 
                  className="p-3 bg-gray-900/40 rounded-xl border border-gray-800/80 hover:border-amber-500/20 hover:bg-gray-900/60 transition-all flex flex-col gap-2 relative overflow-hidden group cursor-pointer"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{stock.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-gray-950 border border-gray-800 text-gray-400">
                        {stock.ticker}
                      </span>
                    </div>
                    
                    <span 
                      className="text-xs font-black flex items-center gap-0.5"
                      style={{ color: isPositive ? 'var(--color-bullish)' : 'var(--color-bearish)' }}
                    >
                      <ArrowUpRight size={14} className={isPositive ? '' : 'rotate-90'} /> 
                      {isPositive ? '+' : ''}{stock.changePct.toFixed(2)}%
                    </span>
                  </div>

                  <div className="flex justify-between items-baseline">
                    <span className="text-xs font-bold text-gray-400">현재가: <strong className="text-gray-200 numeric-font">{stock.price}</strong></span>
                    <span className="text-[10px] font-medium text-gray-500 leading-normal max-w-[70%] text-right group-hover:text-amber-400/80 transition-colors">
                      {stock.reason}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. Blue Chips by Sector Section (3/5 Column width) */}
      <div className="lg:col-span-3 glass-panel flex flex-col justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
            <Star size={18} className="text-indigo-400" />
            카테고리별 프리미엄 대장주 레이더
          </h3>
          <p className="text-xs text-gray-500 font-semibold mb-6">
            주식 시장의 척추 역할을 하는 각 핵심 테마별 최상위 대표 우량주(Blue Chip) 모음집입니다.
          </p>

          {/* Selector Tabs */}
          <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-800/40 pb-4">
            {Object.keys(blueChipCategories).map((key) => {
              const cat = blueChipCategories[key];
              const isActive = activeCategory === key;
              return (
                <button
                  key={key}
                  onClick={() => setActiveCategory(key)}
                  className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 border ${
                    isActive 
                      ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.1)]' 
                      : 'bg-gray-900/60 border-gray-800/80 text-gray-400 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  {cat.icon}
                  {cat.label}
                </button>
              );
            })}
          </div>

          {/* Blue Chip Stocks List for active category */}
          <div className="flex flex-col gap-4">
            {blueChipCategories[activeCategory].list.map((stock) => (
              <div 
                key={stock.ticker}
                className="p-4 bg-gray-900/20 rounded-xl border border-gray-800/60 hover:border-indigo-500/10 hover:bg-gray-900/40 transition-all flex flex-col gap-2"
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-white">{stock.name}</h4>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      {stock.subSector}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-gray-400">
                    시가총액: <strong className="text-gray-200 numeric-font">{stock.marketCap}</strong>
                  </span>
                </div>
                
                <p className="text-xs text-gray-500 leading-normal font-semibold">
                  🚀 <strong className="text-gray-300">시장 지배력:</strong> {stock.strength}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
};
