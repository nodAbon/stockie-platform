import React from 'react';

interface ThermometerProps {
  temperature: number; // -100 to 100
  fearGreed: number;
}

export const MarketThermometer: React.FC<ThermometerProps> = ({ temperature, fearGreed }) => {
  // Convert temperature (-100 to 100) to percentage (0% to 100%)
  const percentage = ((temperature + 100) / 200) * 100;
  
  // Decide glowing color based on temperature
  let themeColor = 'var(--color-neutral)';
  let moodEmoji = '🌀';
  let moodText = '눈치보는 횡보장';
  
  if (temperature > 25) {
    themeColor = 'var(--color-bullish)';
    moodEmoji = '🔥';
    moodText = '불타는 상승장';
  } else if (temperature < -25) {
    themeColor = 'var(--color-bearish)';
    moodEmoji = '❄️';
    moodText = '차가운 하락장';
  }

  // Get Fear & Greed label
  let fgLabel = 'Neutral';
  let fgColor = 'var(--color-neutral)';
  if (fearGreed >= 75) {
    fgLabel = 'Extreme Greed (극도 탐욕)';
    fgColor = 'var(--color-bullish)';
  } else if (fearGreed >= 55) {
    fgLabel = 'Greed (탐욕)';
    fgColor = 'var(--color-bullish)';
  } else if (fearGreed <= 25) {
    fgLabel = 'Extreme Fear (극도 공포)';
    fgColor = 'var(--color-bearish)';
  } else if (fearGreed <= 45) {
    fgLabel = 'Fear (공포)';
    fgColor = 'var(--color-bearish)';
  }

  return (
    <div className="glass-panel h-full flex flex-col justify-between">
      <div>
        <h3 className="text-lg font-bold text-gray-200 mb-6 flex items-center gap-2">
          <span>🌡️</span> 시장 종합 감정 레이더
        </h3>
        
        {/* Thermometer Temperature Header */}
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-sm text-gray-400 font-semibold">글로벌 시장 온도</span>
          <span 
            className="text-4xl font-extrabold numeric-font" 
            style={{ color: themeColor, textShadow: `0 0 10px ${themeColor}44` }}
          >
            {temperature > 0 ? `+${temperature}` : temperature}°C
          </span>
        </div>

        {/* Thermometer Bar Layout */}
        <div className="relative w-full h-8 bg-gray-900/60 rounded-full border border-gray-800 overflow-hidden mb-6">
          {/* Centered zero line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-700/80 z-10" />
          
          {/* Active colored fill */}
          <div 
            className="h-full rounded-full transition-all duration-1000 ease-out pulsing-glow"
            style={{
              width: `${Math.abs(temperature)}%`,
              left: temperature >= 0 ? '50%' : 'auto',
              right: temperature < 0 ? '50%' : 'auto',
              position: 'absolute',
              background: `linear-gradient(${temperature >= 0 ? 'to right' : 'to left'}, var(--bg-dark), ${themeColor})`,
            }}
          />
          
          {/* Sliding bubble indicator */}
          <div 
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full border-2 border-white shadow-lg transition-all duration-1000 ease-out z-20"
            style={{ 
              left: `${percentage}%`,
              backgroundColor: themeColor,
              boxShadow: `0 0 12px ${themeColor}`
            }}
          />
        </div>

        {/* Market Mood Badge */}
        <div className="flex items-center gap-3 p-4 bg-gray-900/40 rounded-xl border border-gray-800/50 mb-6">
          <span className="text-3xl">{moodEmoji}</span>
          <div>
            <div className="text-xs text-gray-500 font-bold">MARKET STATE</div>
            <div className="text-base font-extrabold" style={{ color: themeColor }}>
              {moodText}
            </div>
          </div>
        </div>
      </div>

      {/* Fear & Greed Metric */}
      <div>
        <div className="flex justify-between items-center text-sm mb-2">
          <span className="text-gray-400 font-semibold">공포 / 탐욕 지수</span>
          <span className="font-extrabold numeric-font" style={{ color: fgColor }}>
            {fearGreed} / 100
          </span>
        </div>
        <div className="w-full h-2 bg-gray-900 rounded-full overflow-hidden mb-1">
          <div 
            className="h-full transition-all duration-1000 ease-out"
            style={{ 
              width: `${fearGreed}%`, 
              backgroundColor: fgColor 
            }}
          />
        </div>
        <div className="text-right text-xs font-bold text-gray-500">
          {fgLabel}
        </div>
      </div>
    </div>
  );
};
