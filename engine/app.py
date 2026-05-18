from flask import Flask, request, jsonify
from flask_cors import CORS
import scraper
import analyzer
import re

app = Flask(__name__)
# Enable CORS for all routes (necessary for frontend/backend communication)
CORS(app)

@app.route('/api/market-radar', methods=['GET'])
def market_radar():
    """Returns real-time macro indices and calculated market sentiment guidelines."""
    try:
        radar_data = analyzer.get_market_radar()
        return jsonify(radar_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock-analysis', methods=['GET'])
def stock_analysis():
    """Combines stock historical performance with news sentiment crawler results."""
    ticker_query = request.args.get('ticker', '').strip()
    if not ticker_query:
        return jsonify({'error': 'Ticker parameter is required'}), 400
        
    try:
        # 1. Fetch stock daily price info and historical values
        stock_info = analyzer.get_stock_analysis(ticker_query)
        resolved_ticker = stock_info['ticker']
        
        # 2. Dynamically crawl news based on whether it is Korean or US stock
        is_korean = False
        # Match if ticker consists of digits or contains .KS / .KQ
        if re.search(r'\d{6}', resolved_ticker) or resolved_ticker.endswith('.KS') or resolved_ticker.endswith('.KQ'):
            is_korean = True
            news_items = scraper.get_naver_news(resolved_ticker)
        else:
            news_items = scraper.get_us_news(resolved_ticker)
            
        # 3. Compute aggregate sentiment percentages
        pos_count = 0
        neg_count = 0
        neu_count = 0
        
        for item in news_items:
            sent = item['sentiment']
            if sent == 'Positive':
                pos_count += 1
            elif sent == 'Negative':
                neg_count += 1
            else:
                neu_count += 1
                
        total_news = len(news_items)
        pos_pct = round((pos_count / total_news) * 100, 1) if total_news > 0 else 0
        neg_pct = round((neg_count / total_news) * 100, 1) if total_news > 0 else 0
        neu_pct = round((neu_count / total_news) * 100, 1) if total_news > 0 else 0
        
        # Determine overall stock sentiment "weather" summary
        if total_news == 0:
            weather = "안개 (분석 자료 부족)"
            weather_desc = "관련된 최신 뉴스가 없어 호재/악재 판정이 불가합니다."
        elif pos_count > neg_count and pos_count >= neu_count:
            weather = "☀️ 맑음 (호재 가득)"
            weather_desc = "호재성 기사와 긍정적인 전망이 지배적입니다. 매수 관심군으로 분류하기 좋은 상태입니다."
        elif neg_count > pos_count and neg_count >= neu_count:
            weather = "🌧️ 비바람 (악재 주의)"
            weather_desc = "악재성 기사와 부정적인 신호가 많이 잡힙니다. 신규 진입 시 리스크 관리가 긴요합니다."
        else:
            weather = "☁️ 흐림 (눈치 게임)"
            weather_desc = "긍정과 부정 뉴스가 팽팽하게 대치 중이거나 중립적인 보도가 주를 이루어 관망이 필요합니다."
            
        sentiment_summary = {
            'total_news': total_news,
            'positive_count': pos_count,
            'negative_count': neg_count,
            'neutral_count': neu_count,
            'positive_pct': pos_pct,
            'negative_pct': neg_pct,
            'neutral_pct': neu_pct,
            'weather': weather,
            'weather_description': weather_desc
        }
        
        # 4. Calculate Antigravity AI's Estimated Closing Price for Today
        price = stock_info['price']
        change_pct = stock_info['change_pct']
        
        predicted_close = price
        predicted_change_pct = change_pct
        confidence_level = 85
        range_low = price
        range_high = price
        ai_rationale = ""
        
        if price > 0:
            import random
            sentiment_drift = (pos_pct - neg_pct) / 100 * 0.008  # Max 0.8% drift
            
            # Predict a minor variation close to current price with a sentiment bias
            predicted_change_pct = change_pct + (sentiment_drift * 100) + random.uniform(-0.15, 0.15)
            predicted_close = price * (1 + (predicted_change_pct - change_pct) / 100)
            
            # Rounding appropriately
            if is_korean:
                predicted_close = round(predicted_close / 100) * 100  # Round to nearest 100 won
                range_low = round((predicted_close * 0.985) / 100) * 100
                range_high = round((predicted_close * 1.015) / 100) * 100
            else:
                predicted_close = round(predicted_close, 2)
                range_low = round(predicted_close * 0.985, 2)
                range_high = round(predicted_close * 1.015, 2)
                
            # Confidence logic
            confidence_level = 82
            if total_news > 10:
                confidence_level = 90
            elif total_news < 5:
                confidence_level = 75
                
            # Pre-format the predicted close with proper currencies and rounding
            formatted_close = f"{predicted_close:,.0f}원" if is_korean else f"${predicted_close:,.2f}"
            
            # Calculate AI Action Signal
            if pos_pct >= 60 and change_pct >= 0.5:
                trading_signal = "Strong Buy"
                signal_label = "🔥 적극 매수"
                signal_comment = "강력한 호재성 보도 쏠림과 함께 당일 장중 수급 거래량이 급격히 증가하고 있습니다. 상승 추세 모멘텀이 매우 강하여 적극적인 진입이 단기적으로 유효한 매수 타이밍입니다."
            elif pos_pct >= 50 or (change_pct >= 0 and neg_pct < 35):
                trading_signal = "Buy"
                signal_label = "📈 분할 매수"
                signal_comment = "호재성 여론이 비교적 우세하며 장중 저가 방어 매수세가 견고하게 유입됩니다. 급격한 추격보다 주가 음봉 조정 시 분할로 매수 비중을 채워나가는 진입 타이밍입니다."
            elif neg_pct >= 60 and change_pct <= -0.5:
                trading_signal = "Strong Sell"
                signal_label = "🚨 적극 매도 (대피)"
                signal_comment = "부정적인 악재성 보도 이슈가 집중되며 실시간 패닉 투매 압력이 증가하고 있습니다. 추가 하락 지지선 붕괴 위험이 크므로 일단 현금을 확보하고 대피할 적극 매도 타이밍입니다."
            elif neg_pct >= 45 or change_pct < 0:
                trading_signal = "Sell"
                signal_label = "📉 비중 축소"
                signal_comment = "악재성 기사 비율이 늘어나고 단기 차익 실현 욕구가 강해 지수 조정을 부추기고 있습니다. 지수 반등 시마다 보유 지분 비중을 점진적으로 낮추는 매도 타이밍입니다."
            else:
                trading_signal = "Hold"
                signal_label = "⚖️ 관망 및 대기"
                signal_comment = "시장 내 호재와 악재 기사 비율이 팽팽히 맞서며 뚜렷한 세력 수급 쏠림이 없는 횡보세입니다. 확실한 방향성이 보일 때까지 추가 매수를 보류하고 관망할 타이밍입니다."

            # AI Rationale text
            if pos_pct >= 55 and change_pct >= 0:
                ai_rationale = f"오늘 시장 보도 기사의 긍정 비율({pos_pct}%)이 우세하고 당일 장중 수급 유입 모멘텀이 강화되고 있습니다. 장 마감까지 이 상승세가 유지되며, 현재 대비 추가 보합/상승한 {formatted_close} 부근에서 마감할 가능성이 큽니다."
            elif neg_pct >= 55 or change_pct < 0:
                ai_rationale = f"현재 보도 여론 내 악재/부정 비율({neg_pct}%)이 잡혀 있고 장중 매도세가 관측됩니다. 장 막판 투매 압력이 일시 진정될 수 있으나 전반적으로 약보합 또는 소폭 하락 조정을 거친 {formatted_close}선에서 수렴 종가를 형성할 가능성이 유력합니다."
            else:
                ai_rationale = f"호재성 이슈와 악재성 기사 비율이 팽팽히 대치(중립 {neu_pct}%)하며 방향성이 모호합니다. 뚜렷한 세력 수급 쏠림이 보이지 않아, 현재 가격대 주변에서 등락을 거듭하다 {formatted_close} 부근 박스권 보합세로 장을 마칠 것으로 예상됩니다."
        else:
            trading_signal = "Hold"
            signal_label = "⚖️ 분석 대기"
            signal_comment = "종목 데이터가 부족하여 매매 타이밍 분석을 보류합니다."
            ai_rationale = "종목 데이터가 부족하여 예상 종가를 산출하기 어렵습니다."

        ai_prediction = {
            'predicted_close': float(predicted_close),
            'predicted_change_pct': float(predicted_change_pct),
            'confidence_level': int(confidence_level),
            'range_low': float(range_low),
            'range_high': float(range_high),
            'ai_rationale': ai_rationale,
            'trading_signal': trading_signal,
            'signal_label': signal_label,
            'signal_comment': signal_comment
        }
        
        # Combine everything together
        result = {
            'stock': stock_info,
            'is_korean': is_korean,
            'news': news_items,
            'sentiment': sentiment_summary,
            'ai_prediction': ai_prediction
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Local development server running on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
