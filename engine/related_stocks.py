"""
related_stocks.py — Horae(호재)-theme based related stock recommender.

v3 Changes vs v2:
  - NO longer recommends by sector alone.
  - Detects the actual HORAE THEME from the stock's positive news headlines.
  - Recommends stocks that benefit from the SAME catalyst/theme.
  - Falls back to curated supply-chain map if news is empty.
"""

import yfinance as yf

# ── Horae Theme Detection ─────────────────────────────────────────────────
# Maps keyword lists → theme keys
THEME_KEYWORDS = {
    "AI_반도체": ["AI", "인공지능", "HBM", "GPU", "데이터센터", "nvidia", "artificial intelligence",
                "반도체", "파운드리", "첨단", "on-device", "엣지AI"],
    "방산_수출":  ["방산", "수출", "무기", "전쟁", "국방", "군", "K-방산", "수주", "미사일", "레이더",
                "폴란드", "호주", "중동", "NATO", "defense"],
    "배터리_EV":  ["배터리", "전기차", "EV", "양극재", "음극재", "리튬", "니켈", "분리막", "충전",
                "battery", "electric vehicle", "BEV"],
    "바이오_신약": ["바이오", "신약", "FDA", "임상", "허가", "항암", "면역", "글로벌 임상",
                 "기술수출", "라이선스", "파이프라인", "biotech", "drug"],
    "수출_환율":  ["수출", "환율", "달러", "원화 약세", "무역흑자", "미국 수출", "글로벌 수요"],
    "금리_인하":  ["금리인하", "금리 인하", "Fed", "피벗", "기준금리", "인하", "완화", "유동성"],
    "원자재_상승": ["원자재", "철강", "구리", "알루미늄", "포스코", "원유", "LNG", "가스", "commodity"],
    "중국_회복":  ["중국", "차이나", "중국 수요", "리오프닝", "경기부양", "중국 시장", "내수"],
    "반도체_장비": ["장비", "증착", "식각", "EUV", "노광", "CVD", "ALD", "장비 수주", "Capex"],
    "부동산_건설": ["부동산", "건설", "아파트", "분양", "재건축", "건설 수주", "SOC"],
    "플랫폼_광고": ["광고", "플랫폼", "쇼핑", "커머스", "검색", "유튜브", "트래픽", "MAU"],
}

# ── Theme → Beneficiary Stocks ─────────────────────────────────────────────
THEME_STOCKS = {
    "AI_반도체": [
        {"ticker": "042700", "name": "한미반도체",    "relation": "HBM TC-Bonder 독점 장비 → AI 호재 직결", "tag": "반도체장비"},
        {"ticker": "000660", "name": "SK하이닉스",   "relation": "NVDA HBM 독점 공급 → AI 수요 최대 수혜", "tag": "메모리"},
        {"ticker": "NVDA",   "name": "Nvidia",       "relation": "AI 반도체 글로벌 대장주",               "tag": "AI"},
        {"ticker": "TSM",    "name": "TSMC",         "relation": "AI칩 독점 파운드리, 고마진 성장",        "tag": "파운드리"},
        {"ticker": "357780", "name": "솔브레인",     "relation": "반도체 공정 소재 → AI Capex 수혜",      "tag": "소재"},
        {"ticker": "240810", "name": "원익IPS",      "relation": "AI 설비 증가 → 장비 수주 급증 수혜",    "tag": "반도체장비"},
    ],
    "방산_수출": [
        {"ticker": "012450", "name": "한화에어로스페이스", "relation": "K-방산 수출 1위, 폴란드·중동 수주 직접 수혜", "tag": "방산"},
        {"ticker": "047810", "name": "한국항공우주(KAI)",  "relation": "KF-21 수출 + FA-50 동반 수혜",          "tag": "방산"},
        {"ticker": "064350", "name": "현대로템",      "relation": "K2 전차 수출 + 폴란드 계약 직수혜",     "tag": "방산"},
        {"ticker": "272210", "name": "한화시스템",    "relation": "전자전·레이더 방산 계열사",             "tag": "방산"},
        {"ticker": "LMT",    "name": "Lockheed Martin","relation": "글로벌 방산 수요 증가 최대 수혜 대형주", "tag": "방산"},
    ],
    "배터리_EV": [
        {"ticker": "373220", "name": "LG에너지솔루션","relation": "글로벌 EV 배터리 2위, EV 수요 직결",   "tag": "배터리"},
        {"ticker": "247540", "name": "에코프로비엠",  "relation": "양극재 1위 → 배터리 호재 직수혜",      "tag": "양극재"},
        {"ticker": "006400", "name": "삼성SDI",      "relation": "프리미엄 EV 배터리 고마진 공급사",      "tag": "배터리"},
        {"ticker": "302440", "name": "SK아이이테크놀로지","relation": "분리막 공급 → 배터리 증설 수혜",   "tag": "분리막"},
        {"ticker": "005490", "name": "POSCO홀딩스",  "relation": "리튬·니켈 소재 공급 + 양극재 계열사",  "tag": "소재"},
    ],
    "바이오_신약": [
        {"ticker": "207940", "name": "삼성바이오로직스","relation": "CMO 바이오 1위 → 신약 임상 수혜",    "tag": "바이오"},
        {"ticker": "068270", "name": "셀트리온",      "relation": "바이오시밀러 FDA 허가 모멘텀",         "tag": "바이오"},
        {"ticker": "196170", "name": "알테오젠",      "relation": "SC플랫폼 글로벌 기술수출 선두",        "tag": "바이오"},
        {"ticker": "128940", "name": "한미약품",      "relation": "GLP-1 비만치료제 기술수출 파이프라인", "tag": "제약"},
        {"ticker": "000100", "name": "유한양행",      "relation": "레이저티닙 FDA 허가 모멘텀",           "tag": "제약"},
    ],
    "수출_환율": [
        {"ticker": "005380", "name": "현대자동차",    "relation": "수출 비중 80%+, 달러 강세 직접 수혜", "tag": "완성차"},
        {"ticker": "000660", "name": "SK하이닉스",   "relation": "달러 매출 100%, 환율 수혜 최대",       "tag": "반도체"},
        {"ticker": "005930", "name": "삼성전자",     "relation": "글로벌 수출 1위 기업, 환율 레버리지", "tag": "전자"},
        {"ticker": "012450", "name": "한화에어로스페이스","relation": "방산 수출 달러 결제 직수혜",        "tag": "방산"},
        {"ticker": "047810", "name": "한국항공우주(KAI)","relation": "수출 항공기 달러 결제",              "tag": "방산"},
    ],
    "금리_인하": [
        {"ticker": "105560", "name": "KB금융",       "relation": "금리인하 시 대출 수요 증가 + NIM 주시", "tag": "금융"},
        {"ticker": "055550", "name": "신한지주",     "relation": "저PBR 금융주 밸류업 + 금리 수혜",      "tag": "금융"},
        {"ticker": "086790", "name": "하나금융지주", "relation": "고배당 금융주, 금리인하 리레이팅 기대", "tag": "금융"},
        {"ticker": "AAPL",   "name": "Apple",       "relation": "금리인하 = 성장주 밸류에이션 상승",     "tag": "성장주"},
        {"ticker": "NVDA",   "name": "Nvidia",      "relation": "금리인하 = AI 투자 Capex 가속 수혜",   "tag": "AI"},
    ],
    "원자재_상승": [
        {"ticker": "005490", "name": "POSCO홀딩스",  "relation": "철강·리튬 원자재 가격 상승 직수혜",   "tag": "소재"},
        {"ticker": "010130", "name": "고려아연",     "relation": "아연·금·은 비철금속 가격 상승 수혜",  "tag": "비철금속"},
        {"ticker": "097950", "name": "CJ제일제당",   "relation": "곡물 가격 → 식품 원가 영향 주목",     "tag": "식품"},
        {"ticker": "034730", "name": "SK",           "relation": "에너지·화학 원자재 관련 지주",         "tag": "에너지"},
    ],
    "중국_회복": [
        {"ticker": "005930", "name": "삼성전자",     "relation": "중국 스마트폰 시장 최대 수혜",         "tag": "전자"},
        {"ticker": "005380", "name": "현대자동차",   "relation": "중국 판매 비중 회복 기대주",           "tag": "완성차"},
        {"ticker": "000660", "name": "SK하이닉스",  "relation": "중국 서버·스마트폰 DRAM 수요 수혜",   "tag": "메모리"},
        {"ticker": "010130", "name": "고려아연",     "relation": "중국 인프라 투자 = 비철금속 수요 증가","tag": "소재"},
        {"ticker": "005490", "name": "POSCO홀딩스",  "relation": "중국 철강 수요 회복 + 배터리 소재",   "tag": "소재"},
    ],
    "반도체_장비": [
        {"ticker": "042700", "name": "한미반도체",   "relation": "HBM 장비 → Capex 증가 최대 수혜",    "tag": "장비"},
        {"ticker": "240810", "name": "원익IPS",     "relation": "CVD/ALD 증착 장비 수주 수혜",         "tag": "장비"},
        {"ticker": "AMAT",   "name": "Applied Materials","relation": "글로벌 반도체 장비 1위",           "tag": "장비"},
        {"ticker": "ASML",   "name": "ASML",        "relation": "EUV 노광 독점, Capex 증가 수혜",      "tag": "장비"},
        {"ticker": "357780", "name": "솔브레인",    "relation": "장비 증설 → 공정 소재 동반 수혜",     "tag": "소재"},
    ],
    "부동산_건설": [
        {"ticker": "000720", "name": "현대건설",     "relation": "국내외 수주 1위 건설사",              "tag": "건설"},
        {"ticker": "047040", "name": "대우건설",     "relation": "해외 플랜트·건설 수주 수혜주",        "tag": "건설"},
        {"ticker": "006360", "name": "GS건설",      "relation": "자이 브랜드 주택 + 해외 수주",        "tag": "건설"},
        {"ticker": "005440", "name": "현대시멘트",   "relation": "건설경기 회복 → 시멘트 수요 수혜",    "tag": "건자재"},
    ],
    "플랫폼_광고": [
        {"ticker": "035420", "name": "NAVER",       "relation": "국내 검색광고·커머스 1위",            "tag": "플랫폼"},
        {"ticker": "035720", "name": "카카오",       "relation": "모바일 광고·커머스 생태계",           "tag": "플랫폼"},
        {"ticker": "META",   "name": "Meta",        "relation": "글로벌 광고 플랫폼 최대 수혜주",      "tag": "플랫폼"},
        {"ticker": "GOOGL",  "name": "Alphabet",   "relation": "검색광고·유튜브 광고 수혜",           "tag": "플랫폼"},
    ],
}

# Curated supply-chain map (used when no news theme detected)
SUPPLY_CHAIN_MAP = {
    "000660": ["AI_반도체", "반도체_장비"],
    "005930": ["AI_반도체", "반도체_장비", "수출_환율"],
    "NVDA":   ["AI_반도체", "반도체_장비"],
    "TSLA":   ["배터리_EV"],
    "373220":  ["배터리_EV"],
    "012450":  ["방산_수출"],
    "005380":  ["수출_환율", "중국_회복"],
    "207940":  ["바이오_신약"],
    "AMD":     ["AI_반도체"],
    "196170":  ["바이오_신약"],
    "068270":  ["바이오_신약"],
    "128940":  ["바이오_신약"],
}

STATIC_FUNDAMENTALS = {
    "042700": {"pe": 28.5,"pb": 6.2, "margin": 22.1,"growth": 45.2},
    "240810": {"pe": 18.3,"pb": 2.8, "margin": 12.4,"growth": 18.5},
    "009150": {"pe": 14.2,"pb": 1.8, "margin": 8.3, "growth": 9.1},
    "357780": {"pe": 22.1,"pb": 3.5, "margin": 18.7,"growth": 22.3},
    "005380": {"pe": 6.8, "pb": 0.72,"margin": 9.2, "growth": 7.5},
    "012330": {"pe": 8.5, "pb": 0.88,"margin": 7.1, "growth": 5.2},
    "002700": {"pe": 5.9, "pb": 0.65,"margin": 11.3,"growth": 8.8},
    "373220": {"pe": 42.1,"pb": 3.2, "margin": 6.8, "growth": 28.4},
    "006400": {"pe": 31.5,"pb": 1.9, "margin": 5.2, "growth": 15.6},
    "247540": {"pe": 35.2,"pb": 5.8, "margin": 15.2,"growth": 35.1},
    "207940": {"pe": 55.3,"pb": 7.1, "margin": 24.8,"growth": 32.5},
    "068270": {"pe": 28.4,"pb": 2.9, "margin": 18.2,"growth": 22.0},
    "128940": {"pe": 85.0,"pb": 9.2, "margin": 12.1,"growth": 41.5},
    "000100": {"pe": 32.1,"pb": 3.1, "margin": 10.5,"growth": 28.0},
    "196170": {"pe": 120.0,"pb":15.3,"margin": 38.5,"growth": 85.2},
    "012450": {"pe": 22.8,"pb": 3.4, "margin": 8.9, "growth": 55.2},
    "047810": {"pe": 18.5,"pb": 1.9, "margin": 6.8, "growth": 38.4},
    "064350": {"pe": 25.2,"pb": 2.1, "margin": 5.5, "growth": 42.0},
    "272210": {"pe": 35.1,"pb": 4.2, "margin": 10.2,"growth": 30.5},
    "005490": {"pe": 15.2,"pb": 0.95,"margin": 12.8,"growth": 18.5},
    "278280": {"pe": 28.5,"pb": 4.1, "margin": 20.3,"growth": 25.0},
    "302440": {"pe": 38.5,"pb": 5.2, "margin": 14.5,"growth": 20.5},
    "000660": {"pe": 18.5,"pb": 1.95,"margin": 21.5,"growth": 42.0},
    "005930": {"pe": 15.2,"pb": 1.55,"margin": 12.5,"growth": 8.5},
    "105560": {"pe": 7.2, "pb": 0.55,"margin": 25.5,"growth": 8.5},
    "055550": {"pe": 7.8, "pb": 0.58,"margin": 22.5,"growth": 9.5},
    "086790": {"pe": 6.5, "pb": 0.48,"margin": 28.5,"growth": 7.5},
    "035420": {"pe": 28.5,"pb": 2.8, "margin": 15.5,"growth": 12.5},
    "035720": {"pe": 55.5,"pb": 2.5, "margin": 5.5, "growth": 5.5},
    "010130": {"pe": 12.5,"pb": 0.85,"margin": 8.5, "growth": 15.5},
    "000720": {"pe": 10.5,"pb": 0.7, "margin": 4.5, "growth": 22.5},
    "047040": {"pe": 9.5, "pb": 0.65,"margin": 3.8, "growth": 18.5},
    "006360": {"pe": 11.5,"pb": 0.75,"margin": 4.2, "growth": 15.5},
    "TSM":   {"pe": 22.1,"pb": 6.8, "margin": 38.2,"growth": 28.5},
    "AVGO":  {"pe": 28.5,"pb": 9.5, "margin": 52.1,"growth": 42.0},
    "AMD":   {"pe": 42.5,"pb": 4.2, "margin": 10.5,"growth": 18.5},
    "SMCI":  {"pe": 15.5,"pb": 3.2, "margin": 8.5, "growth": 85.5},
    "LMT":   {"pe": 18.5,"pb": 12.5,"margin": 9.5, "growth": 5.5},
    "NVDA":  {"pe": 45.5,"pb": 25.5,"margin": 55.5,"growth": 122.0},
    "TSLA":  {"pe": 75.5,"pb": 8.5, "margin": 8.5, "growth": 2.5},
    "AAPL":  {"pe": 28.5,"pb": 45.5,"margin": 25.5,"growth": 5.5},
    "META":  {"pe": 22.5,"pb": 7.5, "margin": 35.5,"growth": 18.5},
    "GOOGL": {"pe": 22.5,"pb": 6.5, "margin": 28.5,"growth": 12.5},
    "JPM":   {"pe": 12.5,"pb": 1.8, "margin": 28.5,"growth": 8.5},
    "AMAT":  {"pe": 25.5,"pb": 8.5, "margin": 26.5,"growth": 18.5},
    "ASML":  {"pe": 38.5,"pb": 15.5,"margin": 28.5,"growth": 12.5},
    "MU":    {"pe": 12.5,"pb": 2.2, "margin": 15.5,"growth": 52.5},
    "ON":    {"pe": 22.5,"pb": 4.5, "margin": 28.5,"growth": 8.5},
}


def detect_horae_themes(news_items: list) -> list:
    """Detect which horae themes are present in the positive news items.

    Returns a list of matched theme keys sorted by match count descending.
    """
    theme_scores = {k: 0 for k in THEME_KEYWORDS}
    positive_titles = [
        n['title'].upper()
        for n in news_items
        if n.get('sentiment') == 'Positive'
    ]
    if not positive_titles:
        # Use all titles if no positives detected
        positive_titles = [n['title'].upper() for n in news_items]

    for title in positive_titles:
        for theme, keywords in THEME_KEYWORDS.items():
            for kw in keywords:
                if kw.upper() in title:
                    theme_scores[theme] += 1

    matched = [(t, s) for t, s in theme_scores.items() if s > 0]
    matched.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in matched]


def _value_score(pe, pb, margin, growth):
    pe_score     = max(0, min(100 - abs(pe - 15) * 2, 100)) if 0 < pe < 200 else 0.0
    pb_score     = max(0, min(100 - abs(pb - 1.5) * 15, 100)) if pb > 0 else 0.0
    margin_score = min(max(margin * 2, 0), 100)
    growth_score = min(max(50 + growth * 0.8, 0), 100)
    return round(pe_score * 0.30 + pb_score * 0.20 + margin_score * 0.30 + growth_score * 0.20, 1)


def _fetch_fundamentals(ticker):
    try:
        info   = yf.Ticker(ticker).info or {}
        pe     = float(info.get('trailingPE') or info.get('forwardPE') or 0)
        pb     = float(info.get('priceToBook') or 0)
        margin = float(info.get('profitMargins') or 0) * 100
        growth = float(info.get('revenueGrowth') or 0) * 100
        if pe > 0 or pb > 0:
            return {"pe": round(pe,1), "pb": round(pb,2), "margin": round(margin,1), "growth": round(growth,1), "source": "live"}
    except Exception:
        pass
    static = STATIC_FUNDAMENTALS.get(ticker.upper(), {})
    return {**static, "source": "curated"} if static else {"pe": 0, "pb": 0, "margin": 0, "growth": 0, "source": "unknown"}


def _fetch_price(ticker: str) -> dict:
    """Fetch current price, target, and daily change for a ticker.
    Korean: Naver XML chart (close vs open for daily_change_pct).
    US: yfinance info.
    Returns { current_price, target_price, upside_pct, daily_change_pct, currency, price_note }
    """
    import requests as _req
    import xml.etree.ElementTree as _ET
    import re as _re

    clean = ticker.upper()
    is_korean = clean.isdigit() or clean.endswith('.KS') or clean.endswith('.KQ')
    code = _re.sub(r'\D', '', clean)[:6] if is_korean else clean

    if is_korean and code:
        try:
            url = f'https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=5&requestType=0'
            res = _req.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            xml = res.content.decode('euc-kr', errors='replace')
            xml = xml.replace('encoding="EUC-KR"', 'encoding="UTF-8"', 1)
            root = _ET.fromstring(xml)
            items = root.findall('.//item')
            if items:
                last_data = items[-1].get('data', '').split('|')
                # Format: 날짜|시가|고가|저가|종가|거래량
                if len(last_data) >= 5:
                    open_price  = float(last_data[1])  # 시가
                    close_price = float(last_data[4])  # 종가
                    daily_change_pct = round((close_price - open_price) / open_price * 100, 2) if open_price > 0 else 0.0
                    fd = STATIC_FUNDAMENTALS.get(code, {})
                    pb = fd.get('pb', 2.0)
                    upside = 1.20 if pb < 1.0 else 1.15 if pb < 2.0 else 1.08
                    target = round((close_price * upside) / 100) * 100
                    return {
                        'current_price':    int(close_price),
                        'open_price':       int(open_price),
                        'target_price':     int(target),
                        'upside_pct':       round((upside - 1) * 100, 0),
                        'daily_change_pct': daily_change_pct,
                        'currency':         'KRW',
                        'price_note':       '네이버 당일 종가'
                    }
        except Exception:
            pass
    else:
        try:
            info = yf.Ticker(ticker).info or {}
            price       = float(info.get('currentPrice') or info.get('regularMarketPrice') or 0)
            open_price  = float(info.get('regularMarketOpen') or info.get('open') or price)
            target      = float(info.get('targetMeanPrice') or 0)
            daily_change_pct = round((price - open_price) / open_price * 100, 2) if open_price > 0 else 0.0
            if price > 0:
                upside_pct = round(((target / price) - 1) * 100, 1) if target > 0 else 10.0
                return {
                    'current_price':    round(price, 2),
                    'open_price':       round(open_price, 2),
                    'target_price':     round(target, 2) if target > 0 else round(price * 1.12, 2),
                    'upside_pct':       upside_pct,
                    'daily_change_pct': daily_change_pct,
                    'currency':         'USD',
                    'price_note':       '애널리스트 컨센서스 목표가' if target > 0 else '추정 목표가'
                }
        except Exception:
            pass

    return {
        'current_price': 0, 'open_price': 0, 'target_price': 0,
        'upside_pct': 0, 'daily_change_pct': 0,
        'currency': 'KRW' if is_korean else 'USD', 'price_note': '가격 조회 실패'
    }



def _build_result(candidate, primary_ticker):
    t = candidate['ticker']
    clean_primary = primary_ticker.upper().replace('.KS','').replace('.KQ','')
    if t.upper() in (clean_primary, primary_ticker.upper()):
        return None
    fd    = _fetch_fundamentals(t)
    price = _fetch_price(t)
    score = _value_score(fd['pe'], fd['pb'], fd['margin'], fd['growth'])
    grade, color = ("💎 고가치","emerald") if score >= 70 else ("📊 적정","amber") if score >= 50 else ("⚠️ 고평가","red")
    highlights = []
    if fd['margin'] >= 15:              highlights.append(f"고수익성 (이익률 {fd['margin']}%)")
    if 0 < fd['pb'] < 2.0:             highlights.append(f"저PBR {fd['pb']} (자산 대비 저평가)")
    if 0 < fd['pe'] < 20:              highlights.append(f"저PER {fd['pe']} (이익 대비 저평가)")
    if fd['growth'] >= 20:             highlights.append(f"매출 고성장 +{fd['growth']}%")
    if not highlights:                 highlights.append("호재 테마 동반 수혜주")
    return {
        "ticker": t, "name": candidate['name'],
        "relation": candidate['relation'], "tag": candidate['tag'],
        "pe": fd['pe'], "pb": fd['pb'], "margin": fd['margin'], "growth": fd['growth'],
        "current_price":    price['current_price'],
        "target_price":     price['target_price'],
        "upside_pct":       price['upside_pct'],
        "daily_change_pct": price['daily_change_pct'],
        "currency":         price['currency'],
        "price_note":       price['price_note'],

        "value_score": score, "value_grade": grade, "grade_color": color,
        "highlights": highlights, "data_source": fd['source']
    }


def get_related_stocks(ticker: str, news_items: list = None) -> dict:
    """Return horae-theme based related stock recommendations.

    Returns:
        {
          'detected_themes': [...],
          'theme_reason': '...',
          'related': [...]
        }
    """
    clean = ticker.upper().strip().replace('.KS','').replace('.KQ','')
    news_items = news_items or []

    # 1. Detect horae themes from news
    detected_themes = detect_horae_themes(news_items)

    # 2. If no theme from news, use curated supply-chain map
    if not detected_themes:
        detected_themes = SUPPLY_CHAIN_MAP.get(clean, [])

    # 3. Gather candidates from matched themes (up to top 2 themes)
    seen = set()
    candidates = []
    for theme in detected_themes[:2]:
        for stock in THEME_STOCKS.get(theme, []):
            if stock['ticker'] not in seen:
                seen.add(stock['ticker'])
                candidates.append(stock)

    # 4. If still empty, use AI semiconductor as universal default
    if not candidates:
        detected_themes = ["AI_반도체"]
        for stock in THEME_STOCKS["AI_반도체"]:
            if stock['ticker'] not in seen:
                seen.add(stock['ticker'])
                candidates.append(stock)

    # 5. Build results with value scoring
    results = []
    for c in candidates:
        r = _build_result(c, clean)
        if r:
            results.append(r)

    results.sort(key=lambda x: x['value_score'], reverse=True)

    # Human-readable theme reason
    theme_labels = {
        "AI_반도체":  "🤖 AI·반도체 호재",
        "방산_수출":  "🛡️ 방산·수출 호재",
        "배터리_EV":  "🔋 배터리·EV 호재",
        "바이오_신약":"💊 바이오·신약 호재",
        "수출_환율":  "💱 수출·환율 호재",
        "금리_인하":  "📉 금리인하 호재",
        "원자재_상승":"⛏️ 원자재 상승 호재",
        "중국_회복":  "🐉 중국 경기회복 호재",
        "반도체_장비":"🔧 반도체 장비 수요 호재",
        "부동산_건설":"🏗️ 부동산·건설 호재",
        "플랫폼_광고":"📱 플랫폼·광고 호재",
    }
    theme_reason = " + ".join(theme_labels.get(t, t) for t in detected_themes[:2]) if detected_themes else "전반적 시장 호재"

    return {
        "detected_themes": detected_themes[:2],
        "theme_reason": theme_reason,
        "related": results[:5]
    }
