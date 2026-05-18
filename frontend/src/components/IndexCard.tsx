import React, { useState } from 'react';
import { TrendingUp, TrendingDown, HelpCircle } from 'lucide-react';

interface IndexCardProps {
  name: string;
  price: number;
  changePct: number;
}

export const IndexCard: React.FC<IndexCardProps> = ({ name, price, changePct }) => {
  const [showInfo, setShowInfo] = useState<boolean>(false);
  const isPositive = changePct >= 0;
  
  // Custom display name mapping for Korean translation
  const displayNames: { [key: string]: string } = {
    'KOSPI': '코스피 (KOSPI)',
    'KOSDAQ': '코스닥 (KOSDAQ)',
    'SP500': 'S&P 500',
    'NASDAQ': '나스닥 (NASDAQ)',
    'USD_KRW': '원달러 환율 (USD/KRW)',
    'US_10Y_YIELD': '미국 10년물 국채 금리',
    'VIX': '변동성 지수 (VIX)'
  };

  // Detailed descriptions for hover card
  const descriptions: { [key: string]: string } = {
    'KOSPI': '대한민국 대표 유가증권시장 종합지수입니다. 국내 코스피 대기업의 가중 합산 지표로, 원달러 환율 변동 및 외국인 메이저 자금의 유입/유출 추세에 가장 강력하게 반응합니다.',
    'KOSDAQ': '대한민국 코스닥시장 지수입니다. IT, 바이오, 2차전지 등 하이테크 벤처/성장 기업들이 밀집되어 있어, 글로벌 유동성 팽창 시기에 가장 높은 상승 탄력성을 보입니다.',
    'SP500': '미국 증시 500대 기업 종합 주가지수입니다. 전 세계 펀드매니저들이 포트폴리오 벤치마크로 삼는 글로벌 금융 시장의 중추이자 가장 대표적인 경기 상황판입니다.',
    'NASDAQ': '기술주와 미래 성장주 중심의 미국 나스닥 종합 지수입니다. 미국 금리 추이에 극도로 민감하며, 미래 가치를 조기 선반영하는 기술 거대 공룡(Big Tech)들의 격전지입니다.',
    'USD_KRW': '원화 대비 미 달러화의 실시간 교환 환율입니다. 환율 급등(원화 약세) 시 외인 자금 투매 및 대형 기술주의 낙폭 확대를 자극하고, 환율 하락 시 지수 방어 수급이 촉진됩니다.',
    'US_10Y_YIELD': '미국 정부가 보증하는 10년 만기 국채의 수익률입니다. 무위험 금융 자산의 이자율 표준으로, 금리 급등 시 안전자산 쏠림이 생겨 성장주 할인율이 높아져 악재로 작용합니다.',
    'VIX': 'S&P 500 옵션 가격을 기반으로 산출하는 시장의 기대 변동성(공포) 지수입니다. 지표가 20pt를 돌파할수록 시장 참여자들의 극심한 패닉 셀링 및 불확실성이 극대화되고 있음을 의미합니다.'
  };

  // Check if we need formatting (like currency, percentage, etc.)
  let formattedPrice = price.toLocaleString('ko-KR');
  let suffix = '';
  
  if (name === 'USD_KRW') {
    suffix = ' 원';
  } else if (name === 'US_10Y_YIELD') {
    suffix = ' %';
  } else if (name === 'VIX') {
    suffix = ' pt';
  }

  const themeColor = isPositive ? 'var(--color-bullish)' : 'var(--color-bearish)';
  const bgGlass = isPositive 
    ? 'rgba(0, 230, 118, 0.02)' 
    : 'rgba(255, 23, 68, 0.02)';

  return (
    <div 
      className="glass-panel relative overflow-hidden transition-all duration-300 cursor-help select-none hover:scale-[1.02] hover:border-indigo-500/30"
      style={{ 
        background: `linear-gradient(135deg, var(--bg-panel) 0%, ${bgGlass} 100%)`,
        borderColor: isPositive ? 'rgba(0, 230, 118, 0.12)' : 'rgba(255, 23, 68, 0.12)'
      }}
      onMouseEnter={() => setShowInfo(true)}
      onMouseLeave={() => setShowInfo(false)}
    >
      {/* Absolute Information Bubble Overlay */}
      {showInfo && (
        <div className="absolute inset-0 bg-[#0B0E14]/95 backdrop-blur-md rounded-xl p-3 flex flex-col justify-center transition-all duration-300 z-10 border border-indigo-500/20">
          <p className="text-[10px] font-bold text-indigo-400 mb-1 flex items-center gap-1 uppercase tracking-wider">
            <HelpCircle size={10} /> {displayNames[name] || name} 지표 해설
          </p>
          <p className="text-[10px] text-gray-300 leading-normal font-medium">
            {descriptions[name] || '글로벌 거시 경제의 중심 지표로, 지수 방향성에 강력한 모멘텀을 공급합니다.'}
          </p>
        </div>
      )}

      <div className="flex justify-between items-start mb-4">
        <span className="text-xs font-bold text-gray-400">
          {displayNames[name] || name}
        </span>
        <span 
          className="p-1.5 rounded-lg"
          style={{ 
            backgroundColor: isPositive ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255, 23, 68, 0.1)',
            color: themeColor
          }}
        >
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        </span>
      </div>

      <div className="flex items-baseline justify-between">
        <span className="text-xl font-bold numeric-font text-white">
          {formattedPrice}
          <span className="text-xs font-semibold text-gray-400 ml-0.5">{suffix}</span>
        </span>
        
        <span 
          className="text-xs font-bold numeric-font flex items-center gap-0.5"
          style={{ color: themeColor }}
        >
          {isPositive ? '+' : ''}{changePct.toFixed(2)}%
        </span>
      </div>
    </div>
  );
};
