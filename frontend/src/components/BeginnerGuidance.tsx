import React from 'react';
import { HelpCircle, DollarSign, Activity, Award } from 'lucide-react';

interface BeginnerGuidanceProps {
  guidanceText: string;
  fearGreed: number;
}

export const BeginnerGuidance: React.FC<BeginnerGuidanceProps> = ({ guidanceText, fearGreed }) => {
  return (
    <div className="glass-panel h-full flex flex-col justify-between">
      <div>
        <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
          <span>🧠</span> 주린이 투자 전략 디코더
        </h3>
        
        {/* Core Calculated Guidance */}
        <div className="p-4 bg-gray-900/30 rounded-xl border border-gray-800/80 mb-5 leading-relaxed text-sm text-gray-300">
          <p className="font-bold text-white mb-2 flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-indigo-400"><Award size={14} /> AI 투자 행동 지침</span>
            <span className="text-gray-500">시장 심리 강도: <strong className="text-amber-400 numeric-font">{fearGreed}pt</strong></span>
          </p>
          {guidanceText || '현재 지표 데이터를 집계 중입니다...'}
        </div>
      </div>

      {/* Beginner Education Section */}
      <div>
        <h4 className="text-xs font-bold text-gray-400 mb-3 uppercase tracking-wider flex items-center gap-1">
          <HelpCircle size={12} className="text-indigo-400" /> 주식 시장 3대 핵심 룰 설명서
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {/* Exchange Rate Card */}
          <div className="p-3 bg-gray-900/20 rounded-lg border border-gray-800/40">
            <h5 className="font-bold text-gray-300 mb-1 flex items-center gap-1">
              <DollarSign size={12} className="text-amber-400" /> 원달러 환율 상승 = 국장 악재
            </h5>
            <p className="text-gray-500 leading-normal">
              환율이 오르면 원화 가치가 떨어져 국내 증시에 투자했던 외국인 투자자들이 차익 실현 후 유출됩니다. 따라서 환율이 급격히 상승할 때는 국장에 보수적으로 접근하는 것이 좋습니다.
            </p>
          </div>

          {/* Treasury Yields Card */}
          <div className="p-3 bg-gray-900/20 rounded-lg border border-gray-800/40">
            <h5 className="font-bold text-gray-300 mb-1 flex items-center gap-1">
              <Activity size={12} className="text-indigo-400" /> 미국 국채 금리 상승 = 기술주 악재
            </h5>
            <p className="text-gray-500 leading-normal">
              안전 자산인 미국 국채 금리(이자율)가 오르면, 은행이나 채권으로 돈이 몰립니다. 상대적으로 위험한 미래 성장주/기술주의 밸류에이션(적정 가치 평가)이 낮아져 주가가 압박을 받습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
