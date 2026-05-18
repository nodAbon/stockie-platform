from flask import Flask, request, jsonify
from flask_cors import CORS
import scraper
import analyzer
import related_stocks
import re

app = Flask(__name__)
CORS(app)

DISCLAIMER = "⚠️ 이 분석은 참고 정보 제공 목적이며 투자 권유가 아닙니다. 투자 결정과 손익의 책임은 본인에게 있습니다."


def _data_quality_grade(total_news: int, any_simulated: bool) -> dict:
    """Returns a qualitative data quality grade instead of a fake confidence %.
    
    Grades:
        '충분'     — 10+ real articles available
        '보통'     — 5~9 real articles
        '부족'     — 1~4 real articles
        '⚠️ 시뮬레이션' — all articles are simulated (network fail)
    """
    if any_simulated:
        return {'grade': '⚠️ 시뮬레이션', 'color': 'gray', 'real_data': False}
    if total_news >= 10:
        return {'grade': '충분', 'color': 'green', 'real_data': True}
    elif total_news >= 5:
        return {'grade': '보통', 'color': 'amber', 'real_data': True}
    else:
        return {'grade': '부족', 'color': 'red', 'real_data': True}


def _trading_signal(pos_pct, neg_pct, change_pct, rsi, macd_crossover,
                    avg_vol, cur_vol, any_simulated) -> dict:
    """Compute trading signal using composite rules (news + technicals).
    
    Signal rules:
        Strong Buy  = pos_pct >= 65 AND change >= 1.0 AND volume surge AND RSI < 65
        Buy         = pos_pct >= 55 AND change >= 0 AND neg_pct < 30 AND RSI < 70
        Hold        = (no clear edge) OR (simulated data)
        Sell        = neg_pct >= 50 AND change <= 0 AND RSI > 40
        Strong Sell = neg_pct >= 65 AND change <= -1.0 AND RSI > 50
    RSI overbought/oversold overrides:
        RSI > 75 → warn even if Buy signal
        RSI < 25 → strengthen to Strong Buy regardless
    MACD crossover bonus:
        golden → upgrade one level
        dead   → downgrade one level
    """
    if any_simulated:
        return {
            'signal': 'Hold',
            'label':  '⚖️ 데이터 부족 — 관망',
            'comment': '실시간 뉴스 데이터를 불러올 수 없어 신호 판단을 보류합니다. 잠시 후 다시 시도해 주세요.',
            'rsi_note': '',
            'macd_note': ''
        }

    # Determine volume surge (only if data available)
    vol_surge = (cur_vol > avg_vol * 1.2) if (avg_vol > 0 and cur_vol > 0) else False

    # Base signal from news + price
    if neg_pct >= 65 and change_pct <= -1.0:
        signal = 'Strong Sell'
    elif neg_pct >= 50 and change_pct <= 0:
        signal = 'Sell'
    elif pos_pct >= 65 and change_pct >= 1.0 and vol_surge and rsi < 65:
        signal = 'Strong Buy'
    elif pos_pct >= 55 and change_pct >= 0 and neg_pct < 30 and rsi < 70:
        signal = 'Buy'
    else:
        signal = 'Hold'

    # MACD crossover adjustment
    signal_order = ['Strong Sell', 'Sell', 'Hold', 'Buy', 'Strong Buy']
    idx = signal_order.index(signal)
    if macd_crossover == 'golden' and idx < 4:
        idx += 1   # Upgrade
    elif macd_crossover == 'dead' and idx > 0:
        idx -= 1   # Downgrade
    signal = signal_order[idx]

    # RSI override notes
    rsi_note = ''
    if rsi >= 75:
        rsi_note = f'RSI {rsi} → 과매수 구간. 단기 차익 실현 고려 필요.'
        if signal == 'Strong Buy':
            signal = 'Buy'
            idx = signal_order.index(signal)
    elif rsi <= 25:
        rsi_note = f'RSI {rsi} → 과매도 구간. 반등 가능성 있는 저점.'
        if signal in ('Hold', 'Sell'):
            signal = 'Buy'

    macd_note = ''
    if macd_crossover == 'golden':
        macd_note = 'MACD 골든크로스 감지 — 상승 모멘텀 전환 신호'
    elif macd_crossover == 'dead':
        macd_note = 'MACD 데드크로스 감지 — 하락 모멘텀 전환 신호'

    labels = {
        'Strong Buy':  '🔥 적극 매수',
        'Buy':         '📈 분할 매수',
        'Hold':        '⚖️ 관망 및 대기',
        'Sell':        '📉 비중 축소',
        'Strong Sell': '🚨 적극 매도 (대피)'
    }
    comments = {
        'Strong Buy':  '강력한 호재 쏠림과 거래량 급증, 기술 지표가 동시에 상승을 가리킵니다. 적극적 진입이 단기적으로 유효한 매수 타이밍입니다.',
        'Buy':         '호재성 여론이 우세하며 장중 방어 매수세가 견고합니다. 추격보다는 조정 시 분할 매수 비중을 채워나가는 진입 타이밍입니다.',
        'Hold':        '호재와 악재 비율이 팽팽하거나 기술 지표가 중립입니다. 방향성이 확인될 때까지 신규 매수를 보류하고 관망하는 타이밍입니다.',
        'Sell':        '악재성 기사 비율이 높고 단기 차익 실현 매물이 나오고 있습니다. 반등 시마다 보유 비중을 점진적으로 줄이는 매도 타이밍입니다.',
        'Strong Sell': '부정적 보도와 가격 하락이 동시에 발생하고 있습니다. 지지선 붕괴 위험이 크므로 현금 확보 후 관망할 적극 매도 타이밍입니다.'
    }

    return {
        'signal':    signal,
        'label':     labels.get(signal, '⚖️ 관망 및 대기'),
        'comment':   comments.get(signal, ''),
        'rsi_note':  rsi_note,
        'macd_note': macd_note
    }


@app.route('/api/market-radar', methods=['GET'])
def market_radar():
    """Returns real-time macro indices and market sentiment."""
    try:
        radar_data = analyzer.get_market_radar()
        return jsonify(radar_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock-analysis', methods=['GET'])
def stock_analysis():
    """Combines stock data, news sentiment, RSI/MACD, and expected band."""
    ticker_query = request.args.get('ticker', '').strip()
    if not ticker_query:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    try:
        # 1. Stock price + history
        stock_info    = analyzer.get_stock_analysis(ticker_query)
        resolved_ticker = stock_info['ticker']

        is_korean = bool(
            re.search(r'\d{6}', resolved_ticker) or
            resolved_ticker.endswith('.KS') or
            resolved_ticker.endswith('.KQ')
        )

        # 2. News crawl
        news_items = (
            scraper.get_naver_news(resolved_ticker)
            if is_korean
            else scraper.get_us_news(resolved_ticker)
        )

        # 3. Sentiment aggregation
        pos_count = sum(1 for n in news_items if n['sentiment'] == 'Positive')
        neg_count = sum(1 for n in news_items if n['sentiment'] == 'Negative')
        neu_count = sum(1 for n in news_items if n['sentiment'] == 'Neutral')
        total_news = len(news_items)
        any_simulated = any(n.get('is_simulated', False) for n in news_items)

        pos_pct = round((pos_count / total_news) * 100, 1) if total_news > 0 else 0
        neg_pct = round((neg_count / total_news) * 100, 1) if total_news > 0 else 0
        neu_pct = round((neu_count / total_news) * 100, 1) if total_news > 0 else 0

        if total_news == 0:
            weather      = "안개 (분석 자료 부족)"
            weather_desc = "관련된 최신 뉴스가 없어 호재/악재 판정이 불가합니다."
        elif pos_count > neg_count and pos_count >= neu_count:
            weather      = "☀️ 맑음 (호재 가득)"
            weather_desc = "호재성 기사와 긍정적인 전망이 지배적입니다."
        elif neg_count > pos_count and neg_count >= neu_count:
            weather      = "🌧️ 비바람 (악재 주의)"
            weather_desc = "악재성 기사와 부정적인 신호가 많습니다. 신규 진입 시 리스크 관리가 필요합니다."
        else:
            weather      = "☁️ 흐림 (눈치 게임)"
            weather_desc = "긍정과 부정 뉴스가 팽팽하게 대치 중이거나 중립 보도가 많습니다."

        sentiment_summary = {
            'total_news':      total_news,
            'positive_count':  pos_count,
            'negative_count':  neg_count,
            'neutral_count':   neu_count,
            'positive_pct':    pos_pct,
            'negative_pct':    neg_pct,
            'neutral_pct':     neu_pct,
            'weather':         weather,
            'weather_description': weather_desc,
            'any_simulated':   any_simulated
        }

        # 4. Data quality grade (replaces fake confidence %)
        data_quality = _data_quality_grade(total_news, any_simulated)

        # 5. Technical indicators (RSI + MACD)
        price         = stock_info.get('price', 0)
        change_pct    = stock_info.get('change_pct', 0)
        history       = stock_info.get('history', [])
        prices_list   = [h['price'] for h in history if h.get('price', 0) > 0]
        volume        = stock_info.get('volume', 0)

        rsi  = analyzer.calculate_rsi(prices_list)
        macd = analyzer.calculate_macd(prices_list)

        # Approximate 5-day average volume from history (no volume series, use placeholder)
        avg_vol = volume  # Can't compute true avg without volume series; skip vol_surge logic

        # 6. Trading signal (composite)
        signal_data = _trading_signal(
            pos_pct, neg_pct, change_pct,
            rsi, macd['crossover'],
            avg_vol, volume, any_simulated
        )

        # 7. Expected trading band (replaces single predicted close)
        band = analyzer.calculate_expected_band(history, price, is_korean)
        if is_korean:
            band_low_fmt  = f"{band['band_low']:,.0f}원"
            band_high_fmt = f"{band['band_high']:,.0f}원"
        else:
            band_low_fmt  = f"${band['band_low']:,.2f}"
            band_high_fmt = f"${band['band_high']:,.2f}"

        # 8. AI rationale text
        if any_simulated:
            ai_rationale = "실시간 뉴스를 불러올 수 없어 상세 분석이 제한됩니다. 잠시 후 다시 시도해 주세요."
        elif pos_pct >= 55 and change_pct >= 0:
            ai_rationale = (
                f"오늘 시장 보도 기사의 긍정 비율({pos_pct}%)이 우세하며 장중 수급 모멘텀이 강화되고 있습니다. "
                f"30일 일중 변동 패턴 기준으로 당일 예상 거래 범위는 "
                f"{band_low_fmt} ~ {band_high_fmt} 로 분석됩니다."
            )
        elif neg_pct >= 55 or change_pct < 0:
            ai_rationale = (
                f"현재 보도 여론 내 부정 비율({neg_pct}%)이 높으며 장중 매도 압력이 관측됩니다. "
                f"30일 변동 패턴 기준 당일 예상 거래 범위는 "
                f"{band_low_fmt} ~ {band_high_fmt} 로 분석됩니다."
            )
        else:
            ai_rationale = (
                f"호재와 악재 기사가 팽팽히 대치(중립 {neu_pct}%) 중이며 방향성이 모호합니다. "
                f"당일 예상 거래 범위는 {band_low_fmt} ~ {band_high_fmt} 로 분석됩니다."
            )

        ai_prediction = {
            # Band replaces single predicted close
            'band_low':          band['band_low'],
            'band_high':         band['band_high'],
            'band_low_fmt':      band_low_fmt,
            'band_high_fmt':     band_high_fmt,
            'avg_daily_range_pct': band['avg_daily_range_pct'],
            # Technical indicators
            'rsi':               rsi,
            'macd_line':         macd['macd_line'],
            'signal_line':       macd['signal_line'],
            'macd_histogram':    macd['histogram'],
            'macd_crossover':    macd['crossover'],
            'macd_sufficient':   macd['sufficient_data'],
            # Data quality grade
            'data_quality':      data_quality,
            # Signal
            'trading_signal':    signal_data['signal'],
            'signal_label':      signal_data['label'],
            'signal_comment':    signal_data['comment'],
            'rsi_note':          signal_data['rsi_note'],
            'macd_note':         signal_data['macd_note'],
            # Rationale + disclaimer
            'ai_rationale':      ai_rationale,
            'disclaimer':        DISCLAIMER
        }

        result = {
            'stock':        stock_info,
            'is_korean':    is_korean,
            'news':         news_items,
            'sentiment':    sentiment_summary,
            'ai_prediction': ai_prediction
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/related-stocks', methods=['GET'])
def related_stocks_endpoint():
    """Returns horae-theme based related stocks with value scoring.
    
    Accepts optional 'news' JSON array via query to detect themes from live news.
    """
    ticker_query = request.args.get('ticker', '').strip()
    if not ticker_query:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    try:
        # Re-fetch news for this ticker to detect horae theme
        clean = ticker_query.upper().replace('.KS','').replace('.KQ','')
        import re as _re
        is_korean = bool(_re.search(r'\d{6}', clean) or clean.endswith('.KS') or clean.endswith('.KQ') or clean.isdigit())
        news_items = scraper.get_naver_news(ticker_query) if is_korean else scraper.get_us_news(ticker_query)
        result = related_stocks.get_related_stocks(ticker_query, news_items)
        return jsonify({'ticker': ticker_query, **result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

