import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface HistoryPoint {
  date: string;
  price: number;
}

interface StockChartProps {
  history: HistoryPoint[];
  isPositive: boolean;
}

export const StockChart: React.FC<StockChartProps> = ({ history, isPositive }) => {
  const strokeColor = isPositive ? 'var(--color-bullish)' : 'var(--color-bearish)';
  
  // Custom glassmorphic tooltip for the financial chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div 
          className="p-3 rounded-lg border text-xs"
          style={{
            backgroundColor: 'rgba(11, 14, 20, 0.95)',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(8px)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
          }}
        >
          <p className="text-gray-400 font-semibold mb-1">{payload[0].payload.date}</p>
          <p className="font-extrabold text-white text-sm numeric-font">
            {payload[0].value.toLocaleString('ko-KR')}
          </p>
        </div>
      );
    }
    return null;
  };

  // Find min and max price to calculate dynamic Y-axis padding
  const prices = history.map(h => h.price);
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 100;
  const yPadding = (maxPrice - minPrice) * 0.1 || 10;

  return (
    <div className="w-full h-[220px] mt-4">
      {history.length === 0 ? (
        <div className="w-full h-full flex items-center justify-center text-sm text-gray-500 font-bold bg-gray-900/10 rounded-xl border border-gray-800/40">
          차트를 그릴 수 있는 충분한 시세 데이터가 없습니다.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.25}/>
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="date" 
              tick={{ fill: '#607D8B', fontSize: 10, fontFamily: 'Outfit' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(tick) => tick.substring(5, 10)} // Format "2026-05-18" to "05-18"
            />
            <YAxis 
              domain={[minPrice - yPadding, maxPrice + yPadding]}
              tick={{ fill: '#607D8B', fontSize: 10, fontFamily: 'Outfit' }}
              tickLine={false}
              axisLine={false}
              orientation="right"
              tickFormatter={(tick) => tick.toLocaleString('ko-KR')}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke={strokeColor} 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorPrice)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
