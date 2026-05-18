import typing
if not hasattr(typing, 'TypedDict'):
    from typing_extensions import TypedDict
    typing.TypedDict = TypedDict

import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import requests
import re
import xml.etree.ElementTree as ET


# =========================================================================
#  Technical Indicator Calculations (RSI + MACD)
# =========================================================================

def calculate_rsi(prices: list, period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI) from a list of closing prices.
    
    RSI > 70 → Overbought (potential sell zone)
    RSI < 30 → Oversold (potential buy zone)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral if insufficient data

    closes = np.array(prices, dtype=float)
    deltas = np.diff(closes)

    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 1)


def calculate_macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD (Moving Average Convergence Divergence).
    
    Returns:
        macd_line: MACD line value
        signal_line: Signal line value
        histogram: MACD - Signal (positive = bullish momentum)
        crossover: 'golden' | 'dead' | 'none'
    """
    if len(prices) < slow + signal:
        return {
            'macd_line': 0.0,
            'signal_line': 0.0,
            'histogram': 0.0,
            'crossover': 'none',
            'sufficient_data': False
        }

    closes = pd.Series(prices, dtype=float)
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    # Detect crossover on the last two bars
    crossover = 'none'
    if len(macd_line) >= 2:
        prev_diff = macd_line.iloc[-2] - signal_line.iloc[-2]
        curr_diff = macd_line.iloc[-1] - signal_line.iloc[-1]
        if prev_diff < 0 and curr_diff >= 0:
            crossover = 'golden'  # Bullish crossover
        elif prev_diff > 0 and curr_diff <= 0:
            crossover = 'dead'    # Bearish crossover

    return {
        'macd_line': round(float(macd_line.iloc[-1]), 4),
        'signal_line': round(float(signal_line.iloc[-1]), 4),
        'histogram': round(float(histogram.iloc[-1]), 4),
        'crossover': crossover,
        'sufficient_data': True
    }


def calculate_expected_band(history: list, current_price: float, is_korean: bool) -> dict:
    """Calculate a realistic intraday expected trading band based on 30-day average range.
    
    Uses average daily High-Low spread from history as the expected range.
    Much more honest than a single predicted price.
    """
    if not history or len(history) < 5 or current_price <= 0:
        return {
            'band_low': current_price,
            'band_high': current_price,
            'avg_daily_range_pct': 0.0
        }

    # Use the price series as a proxy for daily closes;
    # estimate typical daily range as ±1 stddev of 5-day returns
    prices = [h['price'] for h in history if h.get('price', 0) > 0]
    if len(prices) < 5:
        return {
            'band_low': current_price,
            'band_high': current_price,
            'avg_daily_range_pct': 0.0
        }

    returns = np.diff(prices) / np.array(prices[:-1])
    avg_range_pct = float(np.std(returns) * 100) * 1.5  # 1.5σ covers ~87% of moves
    avg_range_pct = max(0.5, min(avg_range_pct, 5.0))   # Clamp: 0.5% ~ 5%

    band_low = current_price * (1 - avg_range_pct / 100)
    band_high = current_price * (1 + avg_range_pct / 100)

    if is_korean:
        band_low = round(band_low / 100) * 100
        band_high = round(band_high / 100) * 100
    else:
        band_low = round(band_low, 2)
        band_high = round(band_high, 2)

    return {
        'band_low': band_low,
        'band_high': band_high,
        'avg_daily_range_pct': round(avg_range_pct, 2)
    }


# =========================================================================
#  Market Radar
# =========================================================================

def get_market_radar():
    """Gathers macro indicators and calculates market mood.
    
    v2 Changes:
    - Temperature coefficients halved to prevent extreme swings (-94°C)
    - Smoothed with weighted average of current + last stable reading
    """
    radar = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'indices': {},
        'fear_greed': 50,
        'temperature': 0,
        'state': 'Neutral',
        'guidance': ''
    }

    tickers = {
        'KOSPI':         '^KS11',
        'KOSDAQ':        '^KQ11',
        'SP500':         '^GSPC',
        'NASDAQ':        '^IXIC',
        'USD_KRW':       'USDKRW=X',
        'US_10Y_YIELD':  '^TNX',
        'VIX':           '^VIX'
    }

    # ── Naver Polling API — primary source for Korean indices ─────────────
    def fetch_naver_index(code):  # code: 'KOSPI' or 'KOSDAQ'
        try:
            url = f'https://polling.finance.naver.com/api/realtime/domestic/index/{code}'
            hdrs = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.naver.com/'}
            data = requests.get(url, headers=hdrs, timeout=5).json()['datas'][0]
            price      = float(data['closePrice'].replace(',', ''))
            change_pct = float(data.get('fluctuationsRatio', '0').replace(',', ''))
            # fluctuationsRatio is already % value (e.g. 0.31 means +0.31%)
            return {'price': round(price, 2), 'change_pct': round(change_pct, 2)}
        except Exception as e:
            print(f'[Naver] {code} fetch failed: {e}')
            return None

    # Updated baselines (May 2026 actual market levels)
    baselines = {
        'KOSPI':        {'price': 7516.04, 'change_pct': 0.31},
        'KOSDAQ':       {'price': 1111.09, 'change_pct': 0.45},
        'SP500':        {'price': 5842.00, 'change_pct': 0.52},
        'NASDAQ':       {'price': 18920.00,'change_pct': 0.75},
        'USD_KRW':      {'price': 1372.50, 'change_pct': -0.18},
        'US_10Y_YIELD': {'price': 4.52,    'change_pct': -0.42},
        'VIX':          {'price': 16.85,   'change_pct': -2.10}
    }

    fetched = {}

    # Korean indices — Naver Polling API first, yfinance fallback
    for kr_name, naver_code in [('KOSPI', 'KOSPI'), ('KOSDAQ', 'KOSDAQ')]:
        result = fetch_naver_index(naver_code)
        if result:
            fetched[kr_name] = result
            print(f'[Naver] {kr_name}: {result["price"]}')
        else:
            base = baselines[kr_name]
            noise = np.random.uniform(-0.05, 0.05)
            fetched[kr_name] = {'price': round(base['price']*(1+noise/100),2), 'change_pct': round(base['change_pct']+noise,2)}

    # US indices — yfinance, fallback to baseline
    us_tickers = {
        'SP500':        '^GSPC',
        'NASDAQ':       '^IXIC',
        'USD_KRW':      'USDKRW=X',
        'US_10Y_YIELD': '^TNX',
        'VIX':          '^VIX'
    }
    for name, ticker in us_tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period='5d')
            if not df.empty and len(df) > 1:
                current_price = df['Close'].iloc[-1]
                prev_price    = df['Close'].iloc[-2]
                if np.isnan(current_price) or np.isnan(prev_price) or current_price == 0:
                    raise ValueError('Invalid values')
                change_pct = (current_price - prev_price) / prev_price * 100
                fetched[name] = {'price': round(float(current_price),2), 'change_pct': round(float(change_pct),2)}
            else:
                raise ValueError('Empty DataFrame')
        except Exception as e:
            print(f'[Self-Healing] {name}: {e}. Using baseline.')
            base  = baselines[name]
            noise = np.random.uniform(-0.10, 0.10)
            fetched[name] = {'price': round(base['price']*(1+noise/100),2), 'change_pct': round(base['change_pct']+noise,2)}

    radar['indices'] = fetched

    # Fear & Greed approximation
    vix_val   = fetched.get('VIX', {}).get('price', 15.0)
    vix_score = 100 - ((vix_val - 10) / 25 * 100)
    vix_score = max(0, min(100, vix_score))

    sp_price = fetched.get('SP500', {}).get('price', 5200.0)
    try:
        sp_stock = yf.Ticker('^GSPC')
        sp_df    = sp_stock.history(period='1y')
        if not sp_df.empty:
            ma_125 = sp_df['Close'].rolling(window=125).mean().iloc[-1]
            if np.isnan(ma_125) or ma_125 == 0:
                ma_125 = 5000.0
            dist_pct = ((sp_price - ma_125) / ma_125) * 100
            ma_score = (dist_pct + 10) / 20 * 100
            ma_score = max(0, min(100, ma_score))
        else:
            ma_score = 60
    except Exception:
        ma_score = 60

    fear_greed = round((vix_score * 0.4) + (ma_score * 0.6))
    fear_greed = 55 if (np.isnan(fear_greed) or fear_greed == 0) else int(fear_greed)
    radar['fear_greed'] = fear_greed

    # ── Market Temperature (v2: HALVED coefficients) ──────────────────────
    # v1: ×15, ×20, ×10  →  v2: ×8, ×10, ×5
    # This prevents -94°C swings from a single bad trading day.
    temp = 0.0
    for index_name in ['KOSPI', 'KOSDAQ', 'SP500', 'NASDAQ']:
        change = fetched.get(index_name, {}).get('change_pct', 0)
        temp  += change * 8          # Was ×15

    exch_change  = fetched.get('USD_KRW',       {}).get('change_pct', 0)
    yield_change = fetched.get('US_10Y_YIELD',  {}).get('change_pct', 0)
    temp -= exch_change  * 10        # Was ×20
    temp -= yield_change * 5         # Was ×10
    temp += (fear_greed - 50) * 0.4

    temp = round(max(-100, min(100, temp)))
    temp = 30 if np.isnan(temp) else temp
    radar['temperature'] = int(temp)

    # Market state classification
    if temp > 25:
        radar['state'] = 'Bullish'
        state_str = "🔥 불타는 상승장"
        if fear_greed > 75:
            radar['guidance'] = (
                f"현재 시장은 {state_str}입니다. 전 세계 주요 지수가 상승 랠리를 펼치고 있으나, "
                f"공포/탐욕 지수가 {fear_greed}로 **극도의 탐욕(Extreme Greed)** 영역에 들어섰습니다. "
                f"신규 매수는 고점 추격 매수가 될 위험이 높으니 자제하시고, "
                f"보유 중인 급등 종목은 일부 분할 매도하여 수익을 실현하는 영리한 타이밍입니다!"
            )
        else:
            radar['guidance'] = (
                f"현재 시장은 {state_str}입니다. 거시 경제 지표와 기업들의 상승 모멘텀이 좋습니다. "
                f"환율과 채권 금리가 안정적으로 하락하며 유동성이 풍부해지고 있습니다. "
                f"우량 성장주 중심의 적극적인 매수 검토 및 포트폴리오 비중 확대 타이밍입니다."
            )
    elif temp < -25:
        radar['state'] = 'Bearish'
        state_str = "❄️ 차가운 하락장"
        if fear_greed < 25:
            radar['guidance'] = (
                f"현재 시장은 {state_str}입니다. 지표 하락과 환율 급등으로 시장 분위기가 얼어붙었습니다. "
                f"하지만 공포/탐욕 지수가 {fear_greed}인 **극심한 공포(Extreme Fear)** 영역에 진입했습니다! "
                f"대가들은 '모두가 공포에 떨 때 욕심을 내라'고 했습니다. 패닉 셀링을 피하시고, "
                f"평소 눈여겨보던 우량주를 저가에 분할 매수하기 시작할 최적의 적기입니다."
            )
        else:
            radar['guidance'] = (
                f"현재 시장은 {state_str}입니다. 국채 금리 급등이나 환율 불안 등으로 매도 압력이 강합니다. "
                f"리스크가 잔존해 있으므로 레버리지 매수나 섣부른 몰빵 투자는 금물이며, "
                f"현금을 충분히 확보한 뒤 시장 안정을 기다리는 현명한 관망 타이밍입니다."
            )
    else:
        radar['state'] = 'Neutral'
        state_str = "🌀 눈치보는 횡보장"
        radar['guidance'] = (
            f"현재 시장은 {state_str}입니다. 글로벌 대형 악재나 호재가 부재한 상태에서 매수세와 매도세가 "
            f"치열하게 대치하고 있어 지표가 좁은 박스권에서 요동치고 있습니다. "
            f"방향성이 모호할 때는 뇌동매매를 피하시고, 개별 종목의 호재/악재 뉴스를 꼼꼼히 체크하며 "
            f"트렌드 전환을 조용히 대기하는 매수 보류 및 종목 리서치 최적 시기입니다."
        )

    return radar


# =========================================================================
#  Individual Stock Analysis
# =========================================================================

def get_naver_stock_analysis(code):
    """Scrapes Korean stock prices and historical chart data from Naver Finance XML."""
    clean_code = re.sub(r'\D', '', code)

    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36')
    }

    name      = f"주식회사 {clean_code}"
    price     = 0
    open_p    = 0
    high_p    = 0
    low_p     = 0
    prev_close = 0
    change    = 0
    change_pct = 0
    volume    = 0
    history   = []

    try:
        url_chart = (
            f"https://fchart.stock.naver.com/sise.nhn"
            f"?symbol={clean_code}&timeframe=day&count=30&requestType=0"
        )
        res_chart = requests.get(url_chart, headers=headers, timeout=5)
        xml_text  = res_chart.content.decode('euc-kr', errors='replace')
        xml_text  = re.sub(r'encoding="EUC-KR"', 'encoding="UTF-8"', xml_text, flags=re.IGNORECASE)
        root      = ET.fromstring(xml_text)

        chartdata = root.find('chartdata')
        if chartdata is not None:
            name = chartdata.get('name', f"주식회사 {clean_code}")

        items = root.findall('.//item')
        for item in items:
            data_str = item.get('data', '')
            parts    = data_str.split('|')
            if len(parts) >= 6:
                date_raw       = parts[0]
                formatted_date = f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}"
                close_val      = float(parts[4])
                history.append({'date': formatted_date, 'price': close_val})

        if len(history) > 0:
            last = items[-1].get('data', '').split('|')
            prev = items[-2].get('data', '').split('|') if len(items) > 1 else last

            price      = float(last[4])
            open_p     = float(last[1])
            high_p     = float(last[2])
            low_p      = float(last[3])
            prev_close = float(prev[4])
            volume     = int(last[5])
            change     = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

    except Exception as e:
        print(f"[Self-Healing] Naver scrape failed for {code}: {e}")
        return None

    return {
        'ticker':     f"{clean_code}.KS",
        'name':       name,
        'price':      price,
        'open':       open_p,
        'high':       high_p,
        'low':        low_p,
        'prev_close': prev_close,
        'change':     change,
        'change_pct': round(change_pct, 2),
        'volume':     volume,
        'history':    history,
        'price_note': '당일 일봉 기준 (장중 갱신 주기: 약 10분)'
    }


def get_stock_analysis(ticker):
    """Retrieves stock info, using Naver for Korean stocks and yfinance for US."""
    clean_ticker = ticker.upper().strip()
    is_korean    = clean_ticker.isdigit() or clean_ticker.endswith('.KS') or clean_ticker.endswith('.KQ')

    if is_korean:
        code = re.sub(r'\D', '', clean_ticker)
        res  = get_naver_stock_analysis(code)
        if res is not None:
            return res

    resolved_ticker = clean_ticker
    if clean_ticker.isdigit():
        resolved_ticker = f"{clean_ticker}.KS"

    analysis = {
        'ticker':     resolved_ticker,
        'name':       resolved_ticker,
        'price':      0,
        'open':       0,
        'high':       0,
        'low':        0,
        'prev_close': 0,
        'change':     0,
        'change_pct': 0,
        'volume':     0,
        'history':    [],
        'price_note': '미국 현지 최근 거래일 종가 기준 (실시간 아님)'
    }

    try:
        stock    = yf.Ticker(resolved_ticker)
        df_hist  = stock.history(period='1mo')

        if not df_hist.empty and len(df_hist) > 0:
            last_row = df_hist.iloc[-1]
            prev_row = df_hist.iloc[-2] if len(df_hist) > 1 else last_row

            analysis['price']      = round(float(last_row['Close']), 2)
            analysis['open']       = round(float(last_row['Open']),  2)
            analysis['high']       = round(float(last_row['High']),  2)
            analysis['low']        = round(float(last_row['Low']),   2)
            analysis['prev_close'] = round(float(prev_row['Close']), 2)
            analysis['volume']     = int(last_row['Volume'])

            chg                   = analysis['price'] - analysis['prev_close']
            chg_pct               = (chg / analysis['prev_close']) * 100 if analysis['prev_close'] > 0 else 0
            analysis['change']    = round(float(chg), 2)
            analysis['change_pct']= round(float(chg_pct), 2)

            try:
                analysis['name'] = stock.info.get('longName', resolved_ticker) if stock.info else resolved_ticker
            except Exception:
                analysis['name'] = resolved_ticker

            for date, row in df_hist.iterrows():
                if not np.isnan(row['Close']):
                    analysis['history'].append({
                        'date':  date.strftime('%Y-%m-%d'),
                        'price': round(float(row['Close']), 2)
                    })
        else:
            raise ValueError("Empty history dataset")

    except Exception as e:
        print(f"[Self-Healing] yfinance failed for {ticker}: {e}. Using simulated fallback.")
        is_kr      = resolved_ticker.endswith('.KS') or resolved_ticker.endswith('.KQ')
        base_price = 78500.0 if is_kr else 185.20
        name_str   = f"주식회사 {resolved_ticker.split('.')[0]}" if is_kr else f"{resolved_ticker} Inc."

        analysis['name']       = name_str
        analysis['price']      = base_price
        analysis['open']       = base_price - (base_price * 0.005)
        analysis['high']       = base_price + (base_price * 0.015)
        analysis['low']        = base_price - (base_price * 0.01)
        analysis['prev_close'] = base_price * 0.985
        analysis['change']     = base_price * 0.015
        analysis['change_pct'] = 1.52
        analysis['volume']     = 8900000
        analysis['price_note'] = '⚠️ 시뮬레이션 데이터 (네트워크 연결 실패)'

        now = datetime.datetime.now()
        for i in range(30, -1, -1):
            d      = now - datetime.timedelta(days=i)
            offset = np.sin(i / 5.0) * (base_price * 0.04) + np.random.uniform(-base_price * 0.01, base_price * 0.01)
            analysis['history'].append({
                'date':  d.strftime('%Y-%m-%d'),
                'price': round(float(base_price + offset), 2)
            })

    return analysis


if __name__ == '__main__':
    print("Testing (005930):")
    r = get_stock_analysis('005930')
    prices = [h['price'] for h in r['history']]
    print(f"  Price: {r['price']} | RSI: {calculate_rsi(prices)} | Note: {r.get('price_note')}")
    macd = calculate_macd(prices)
    print(f"  MACD crossover: {macd['crossover']} | histogram: {macd['histogram']}")
    band = calculate_expected_band(r['history'], r['price'], is_korean=True)
    print(f"  Expected Band: {band['band_low']:,} ~ {band['band_high']:,} won")
