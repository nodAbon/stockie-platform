"""related_stocks.py — Dynamic supply-chain & sector-based recommender."""

import yfinance as yf
import numpy as np

# ── Curated relationship map ──────────────────────────────────────────────
RELATED_MAP = {
    "000660": [
        {"ticker": "042700", "name": "한미반도체",   "relation": "HBM 패키징 장비 독점 공급사", "tag": "반도체장비"},
        {"ticker": "357780", "name": "솔브레인",    "relation": "식각·세정 소재 공급사",     "tag": "반도체소재"},
        {"ticker": "009150", "name": "삼성전기",   "relation": "패키지 기판·MLCC 공급사",    "tag": "부품"},
        {"ticker": "240810", "name": "원익IPS",    "relation": "증착·식각 공정 장비 1위",   "tag": "반도체장비"},
        {"ticker": "005490", "name": "POSCO홀딩스","relation": "소재 공급 및 계열사 연관",    "tag": "소재"},
    ],
    "005930": [
        {"ticker": "042700", "name": "한미반도체",   "relation": "TC-Bonder 장비 공급",       "tag": "반도체장비"},
        {"ticker": "009150", "name": "삼성전기",   "relation": "카메라모듈·기판 직공급",     "tag": "부품"},
        {"ticker": "357780", "name": "솔브레인",   "relation": "파운드리 소재 공급사",       "tag": "반도체소재"},
        {"ticker": "000660", "name": "SK하이닉스", "relation": "메모리 동반 수혜주",         "tag": "메모리"},
        {"ticker": "240810", "name": "원익IPS",   "relation": "반도체 증착 장비 공급사",    "tag": "반도체장비"},
    ],
    "NVDA": [
        {"ticker": "TSM",   "name": "TSMC",           "relation": "GPU 독점 파운드리",      "tag": "파운드리"},
        {"ticker": "AVGO",  "name": "Broadcom",        "relation": "AI 네트워킹 칩 수혜",   "tag": "반도체"},
        {"ticker": "AMD",   "name": "AMD",             "relation": "AI GPU 경쟁·대안주",    "tag": "반도체"},
        {"ticker": "SMCI",  "name": "Super Micro",     "relation": "NVDA 서버 OEM 파트너",  "tag": "서버"},
        {"ticker": "000660","name": "SK하이닉스",     "relation": "HBM 독점 공급사",       "tag": "메모리"},
    ],
    "TSLA": [
        {"ticker": "373220","name": "LG에너지솔루션","relation": "원통형 배터리 공급사",     "tag": "배터리"},
        {"ticker": "ON",    "name": "onsemi",          "relation": "SiC 전력반도체 공급사", "tag": "전력반도체"},
        {"ticker": "005380","name": "현대자동차",    "relation": "EV 경쟁사 (가치비교)",    "tag": "완성차"},
        {"ticker": "LEA",   "name": "Lear Corp",       "relation": "전기차 전장 시스템",    "tag": "부품"},
        {"ticker": "AMD",   "name": "AMD",             "relation": "차량용 칩 공급 확대",   "tag": "반도체"},
    ],
    "373220": [
        {"ticker": "247540","name": "에코프로비엠",  "relation": "양극재 독점 공급사",      "tag": "양극재"},
        {"ticker": "302440","name": "SK아이이테크","relation": "분리막 핵심 공급사",       "tag": "분리막"},
        {"ticker": "006400","name": "삼성SDI",      "relation": "배터리 경쟁사 가치비교",   "tag": "배터리"},
        {"ticker": "005490","name": "POSCO홀딩스",  "relation": "리튬·니켈 소재 공급",     "tag": "소재"},
        {"ticker": "278280","name": "천보",         "relation": "전해질 소재 공급사",      "tag": "소재"},
    ],
    "012450": [
        {"ticker": "047810","name": "한국항공우주(KAI)","relation": "KF-21 공동개발사",    "tag": "방산"},
        {"ticker": "064350","name": "현대로템",     "relation": "K2 전차 방산 동반 수출",  "tag": "방산"},
        {"ticker": "272210","name": "한화시스템",   "relation": "전자전·레이더 계열사",    "tag": "방산"},
        {"ticker": "LMT",   "name": "Lockheed Martin","relation": "글로벌 방산 벤치마크",  "tag": "방산"},
    ],
    "005380": [
        {"ticker": "012330","name": "현대모비스",   "relation": "핵심부품 1차 벤더",       "tag": "부품"},
        {"ticker": "002700","name": "기아",         "relation": "동반 성장 형제사",        "tag": "완성차"},
        {"ticker": "011210","name": "현대위아",     "relation": "엔진·모듈 계열사",        "tag": "부품"},
        {"ticker": "TSLA",  "name": "Tesla",        "relation": "EV 직접 경쟁사",          "tag": "EV"},
    ],
    "207940": [
        {"ticker": "068270","name": "셀트리온",     "relation": "바이오시밀러 동반성장",   "tag": "바이오"},
        {"ticker": "128940","name": "한미약품",     "relation": "기술수출 선두 신약사",    "tag": "제약"},
        {"ticker": "000100","name": "유한양행",     "relation": "레이저티닙 FDA 허가사",   "tag": "제약"},
        {"ticker": "196170","name": "알테오젠",     "relation": "SC플랫폼 기술수출",       "tag": "바이오"},
    ],
    "AMD": [
        {"ticker": "NVDA",  "name": "Nvidia",        "relation": "AI GPU 시장 선도 경쟁사", "tag": "반도체"},
        {"ticker": "TSM",   "name": "TSMC",          "relation": "AMD 독점 파운드리",       "tag": "파운드리"},
        {"ticker": "MU",    "name": "Micron",        "relation": "AI 서버 메모리 수혜주",   "tag": "메모리"},
        {"ticker": "INTC",  "name": "Intel",         "relation": "x86 전통 경쟁사",         "tag": "반도체"},
    ],
    "196170": [
        {"ticker": "207940","name": "삼성바이오로직스","relation": "CMO 바이오 플랫폼 1위","tag": "바이오"},
        {"ticker": "068270","name": "셀트리온",     "relation": "바이오시밀러 경쟁 관계",  "tag": "바이오"},
        {"ticker": "128940","name": "한미약품",     "relation": "기술수출 동반 성장주",    "tag": "제약"},
    ],
}

# ── Sector → generic blue-chip pool (fallback for unknown tickers) ────────
SECTOR_POOL = {
    "Technology": [
        {"ticker": "NVDA", "name": "Nvidia",  "relation": "AI 반도체 시장 선도 기업",  "tag": "AI/반도체"},
        {"ticker": "TSM",  "name": "TSMC",    "relation": "글로벌 파운드리 1위",        "tag": "파운드리"},
        {"ticker": "AVGO", "name": "Broadcom","relation": "네트워킹 칩 고수익 기업",   "tag": "반도체"},
        {"ticker": "AMD",  "name": "AMD",     "relation": "AI GPU 고성장 경쟁사",       "tag": "반도체"},
        {"ticker": "ANET", "name": "Arista",  "relation": "AI 데이터센터 네트워크",    "tag": "네트워크"},
    ],
    "반도체": [
        {"ticker": "042700","name": "한미반도체","relation": "HBM 패키징 독점 장비사",  "tag": "장비"},
        {"ticker": "240810","name": "원익IPS",  "relation": "증착·식각 장비 1위",       "tag": "장비"},
        {"ticker": "357780","name": "솔브레인", "relation": "공정 소재 공급사",          "tag": "소재"},
        {"ticker": "009150","name": "삼성전기", "relation": "기판·부품 대형 공급사",    "tag": "부품"},
        {"ticker": "005490","name": "POSCO홀딩스","relation": "소재 공급 관련주",       "tag": "소재"},
    ],
    "Consumer Cyclical": [
        {"ticker": "005380","name": "현대자동차","relation": "글로벌 완성차 저PER 우량주","tag": "완성차"},
        {"ticker": "002700","name": "기아",      "relation": "고마진 PBV 사업 강자",     "tag": "완성차"},
        {"ticker": "012330","name": "현대모비스","relation": "완성차 부품 1차 벤더",     "tag": "부품"},
        {"ticker": "TSLA",  "name": "Tesla",     "relation": "EV 시장 모멘텀 대장주",   "tag": "EV"},
    ],
    "Healthcare": [
        {"ticker": "207940","name": "삼성바이오로직스","relation": "CMO 바이오 글로벌 1위","tag": "바이오"},
        {"ticker": "068270","name": "셀트리온",  "relation": "바이오시밀러 수출 강자",  "tag": "바이오"},
        {"ticker": "128940","name": "한미약품",  "relation": "기술수출 선두 신약 개발사","tag": "제약"},
        {"ticker": "LLY",   "name": "Eli Lilly", "relation": "비만치료제 글로벌 1위",   "tag": "신약"},
    ],
    "Energy": [
        {"ticker": "373220","name": "LG에너지솔루션","relation": "글로벌 배터리 셀 2위","tag": "배터리"},
        {"ticker": "006400","name": "삼성SDI",   "relation": "고수익 배터리 셀 메이커", "tag": "배터리"},
        {"ticker": "247540","name": "에코프로비엠","relation": "양극재 시장 선두사",    "tag": "소재"},
        {"ticker": "005490","name": "POSCO홀딩스","relation": "리튬·니켈 소재 공급사", "tag": "소재"},
    ],
    "Industrials": [
        {"ticker": "012450","name": "한화에어로스페이스","relation": "K-방산 수출 1위","tag": "방산"},
        {"ticker": "047810","name": "한국항공우주(KAI)","relation": "전투기 제조사",  "tag": "방산"},
        {"ticker": "064350","name": "현대로템",  "relation": "K2 전차·철도 수출사",    "tag": "방산"},
        {"ticker": "LMT",   "name": "Lockheed", "relation": "글로벌 방산 벤치마크",   "tag": "방산"},
    ],
    "Financial Services": [
        {"ticker": "105560","name": "KB금융",    "relation": "국내 1위 금융지주",       "tag": "금융"},
        {"ticker": "055550","name": "신한지주",  "relation": "글로벌 확장 금융 그룹",   "tag": "금융"},
        {"ticker": "086790","name": "하나금융지주","relation": "저PBR 고배당 금융주",  "tag": "금융"},
        {"ticker": "JPM",   "name": "JP Morgan", "relation": "글로벌 금융 벤치마크",   "tag": "금융"},
    ],
    "Communication Services": [
        {"ticker": "035420","name": "NAVER",     "relation": "국내 IT 플랫폼 1위",     "tag": "플랫폼"},
        {"ticker": "035720","name": "카카오",    "relation": "모바일 메신저 생태계",    "tag": "플랫폼"},
        {"ticker": "META",  "name": "Meta",      "relation": "글로벌 SNS 플랫폼 1위",  "tag": "플랫폼"},
        {"ticker": "GOOGL", "name": "Alphabet",  "relation": "AI+광고 복합 성장주",    "tag": "AI/플랫폼"},
    ],
    "default": [
        {"ticker": "005930","name": "삼성전자",  "relation": "국내 시총 1위 우량주",   "tag": "대형주"},
        {"ticker": "000660","name": "SK하이닉스","relation": "AI 메모리 고성장주",      "tag": "대형주"},
        {"ticker": "AAPL",  "name": "Apple",     "relation": "글로벌 시총 최상위 우량주","tag": "대형주"},
        {"ticker": "NVDA",  "name": "Nvidia",    "relation": "AI 인프라 대장주",        "tag": "AI"},
        {"ticker": "005380","name": "현대자동차","relation": "저PER 고배당 대형 우량주","tag": "대형주"},
    ],
}

STATIC_FUNDAMENTALS = {
    "042700": {"pe": 28.5,"pb": 6.2,"margin": 22.1,"growth": 45.2},
    "240810": {"pe": 18.3,"pb": 2.8,"margin": 12.4,"growth": 18.5},
    "009150": {"pe": 14.2,"pb": 1.8,"margin": 8.3, "growth": 9.1},
    "357780": {"pe": 22.1,"pb": 3.5,"margin": 18.7,"growth": 22.3},
    "005380": {"pe": 6.8, "pb": 0.72,"margin":9.2, "growth": 7.5},
    "012330": {"pe": 8.5, "pb": 0.88,"margin":7.1, "growth": 5.2},
    "002700": {"pe": 5.9, "pb": 0.65,"margin":11.3,"growth": 8.8},
    "373220": {"pe": 42.1,"pb": 3.2,"margin": 6.8, "growth": 28.4},
    "006400": {"pe": 31.5,"pb": 1.9,"margin": 5.2, "growth": 15.6},
    "247540": {"pe": 35.2,"pb": 5.8,"margin": 15.2,"growth": 35.1},
    "207940": {"pe": 55.3,"pb": 7.1,"margin": 24.8,"growth": 32.5},
    "068270": {"pe": 28.4,"pb": 2.9,"margin": 18.2,"growth": 22.0},
    "128940": {"pe": 85.0,"pb": 9.2,"margin": 12.1,"growth": 41.5},
    "000100": {"pe": 32.1,"pb": 3.1,"margin": 10.5,"growth": 28.0},
    "196170": {"pe": 120.0,"pb":15.3,"margin":38.5,"growth": 85.2},
    "012450": {"pe": 22.8,"pb": 3.4,"margin": 8.9, "growth": 55.2},
    "047810": {"pe": 18.5,"pb": 1.9,"margin": 6.8, "growth": 38.4},
    "064350": {"pe": 25.2,"pb": 2.1,"margin": 5.5, "growth": 42.0},
    "272210": {"pe": 35.1,"pb": 4.2,"margin": 10.2,"growth": 30.5},
    "005490": {"pe": 15.2,"pb": 0.95,"margin":12.8,"growth": 18.5},
    "278280": {"pe": 28.5,"pb": 4.1,"margin": 20.3,"growth": 25.0},
    "302440": {"pe": 38.5,"pb": 5.2,"margin": 14.5,"growth": 20.5},
    "011210": {"pe": 10.5,"pb": 0.82,"margin":6.2, "growth": 8.5},
    "000660": {"pe": 18.5,"pb": 1.95,"margin":21.5,"growth": 42.0},
    "005930": {"pe": 15.2,"pb": 1.55,"margin":12.5,"growth": 8.5},
    "105560": {"pe": 7.2, "pb": 0.55,"margin":25.5,"growth": 8.5},
    "055550": {"pe": 7.8, "pb": 0.58,"margin":22.5,"growth": 9.5},
    "086790": {"pe": 6.5, "pb": 0.48,"margin":28.5,"growth": 7.5},
    "035420": {"pe": 28.5,"pb": 2.8,"margin": 15.5,"growth": 12.5},
    "035720": {"pe": 55.5,"pb": 2.5,"margin": 5.5, "growth": 5.5},
    "TSM":  {"pe": 22.1,"pb": 6.8,"margin": 38.2,"growth": 28.5},
    "AVGO": {"pe": 28.5,"pb": 9.5,"margin": 52.1,"growth": 42.0},
    "ANET": {"pe": 38.5,"pb": 14.2,"margin":30.5,"growth": 22.5},
    "SMCI": {"pe": 15.5,"pb": 3.2,"margin": 8.5, "growth": 85.5},
    "AMD":  {"pe": 42.5,"pb": 4.2,"margin": 10.5,"growth": 18.5},
    "ON":   {"pe": 22.5,"pb": 4.5,"margin": 28.5,"growth": 8.5},
    "LEA":  {"pe": 10.5,"pb": 1.1,"margin": 5.2, "growth": 8.5},
    "LMT":  {"pe": 18.5,"pb": 12.5,"margin":9.5, "growth": 5.5},
    "MU":   {"pe": 12.5,"pb": 2.2,"margin": 15.5,"growth": 52.5},
    "INTC": {"pe": 28.5,"pb": 1.5,"margin": 2.5, "growth": -5.5},
    "NVDA": {"pe": 45.5,"pb": 25.5,"margin":55.5,"growth": 122.0},
    "TSLA": {"pe": 75.5,"pb": 8.5,"margin": 8.5, "growth": 2.5},
    "AAPL": {"pe": 28.5,"pb": 45.5,"margin":25.5,"growth": 5.5},
    "META": {"pe": 22.5,"pb": 7.5,"margin": 35.5,"growth": 18.5},
    "GOOGL":{"pe": 22.5,"pb": 6.5,"margin": 28.5,"growth": 12.5},
    "JPM":  {"pe": 12.5,"pb": 1.8,"margin": 28.5,"growth": 8.5},
    "LLY":  {"pe": 52.5,"pb": 45.5,"margin":25.5,"growth": 28.5},
}


def _value_score(pe, pb, margin, growth):
    if pe <= 0 or pe > 200:
        pe_score = 0.0
    else:
        pe_score = max(0, min(100 - abs(pe - 15) * 2, 100))
    pb_score = max(0, min(100 - abs(pb - 1.5) * 15, 100)) if pb > 0 else 0.0
    margin_score = min(max(margin * 2, 0), 100)
    growth_score = min(max(50 + growth * 0.8, 0), 100)
    return round(pe_score * 0.30 + pb_score * 0.20 + margin_score * 0.30 + growth_score * 0.20, 1)


def _fetch_fundamentals(ticker):
    try:
        info = yf.Ticker(ticker).info or {}
        pe     = float(info.get('trailingPE') or info.get('forwardPE') or 0)
        pb     = float(info.get('priceToBook') or 0)
        margin = float(info.get('profitMargins') or 0) * 100
        growth = float(info.get('revenueGrowth') or 0) * 100
        if pe > 0 or pb > 0:
            return {"pe": round(pe,1), "pb": round(pb,2), "margin": round(margin,1), "growth": round(growth,1), "source": "live"}
    except Exception:
        pass
    static = STATIC_FUNDAMENTALS.get(ticker.upper(), {})
    if static:
        return {**static, "source": "curated"}
    return {"pe": 0, "pb": 0, "margin": 0, "growth": 0, "source": "unknown"}


def _detect_sector(ticker):
    """Detect sector via yfinance; return sector key matching SECTOR_POOL."""
    clean = ticker.upper()
    # Korean stocks — infer sector from curated map presence
    if clean.isdigit() or clean.endswith('.KS') or clean.endswith('.KQ'):
        code = clean[:6]
        # Rough sector inference by code range
        semiconductor_codes = {"000660","005930","042700","240810","357780","009150","278280","302440"}
        battery_codes       = {"373220","006400","247540","005490","302440"}
        defense_codes       = {"012450","047810","064350","272210"}
        health_codes        = {"207940","068270","128940","000100","196170"}
        auto_codes          = {"005380","002700","012330","011210","161390"}
        finance_codes       = {"105560","055550","086790"}
        platform_codes      = {"035420","035720"}
        if code in semiconductor_codes: return "반도체"
        if code in battery_codes:       return "Energy"
        if code in defense_codes:       return "Industrials"
        if code in health_codes:        return "Healthcare"
        if code in auto_codes:          return "Consumer Cyclical"
        if code in finance_codes:       return "Financial Services"
        if code in platform_codes:      return "Communication Services"
        return "default"
    # US stocks — use yfinance sector
    try:
        info   = yf.Ticker(ticker).info or {}
        sector = info.get('sector', '')
        if sector in SECTOR_POOL:
            return sector
    except Exception:
        pass
    return "Technology" if not clean.isdigit() else "default"


def _build_result(candidate, primary_ticker):
    t  = candidate['ticker']
    # Skip recommending the primary stock itself
    primary_clean = primary_ticker.upper().replace('.KS','').replace('.KQ','')
    if t.upper() == primary_clean or t.upper() == primary_ticker.upper():
        return None
    fd    = _fetch_fundamentals(t)
    score = _value_score(fd['pe'], fd['pb'], fd['margin'], fd['growth'])
    if score >= 70:
        grade, color = "💎 고가치",  "emerald"
    elif score >= 50:
        grade, color = "📊 적정",    "amber"
    else:
        grade, color = "⚠️ 고평가",  "red"
    highlights = []
    if fd['margin'] >= 20:       highlights.append(f"고수익성 (이익률 {fd['margin']}%)")
    if fd['pb'] > 0 and fd['pb'] < 2.0: highlights.append(f"저PBR {fd['pb']} (자산 대비 저평가)")
    if fd['pe'] > 0 and fd['pe'] < 20:  highlights.append(f"저PER {fd['pe']} (이익 대비 저평가)")
    if fd['growth'] >= 20:       highlights.append(f"매출 고성장 +{fd['growth']}%")
    if not highlights:           highlights.append("섹터 내 수혜 관련주")
    return {
        "ticker": t, "name": candidate['name'],
        "relation": candidate['relation'], "tag": candidate['tag'],
        "pe": fd['pe'], "pb": fd['pb'], "margin": fd['margin'], "growth": fd['growth'],
        "value_score": score, "value_grade": grade, "grade_color": color,
        "highlights": highlights, "data_source": fd['source']
    }


def get_related_stocks(ticker):
    clean = ticker.upper().strip()
    if clean.endswith('.KS') or clean.endswith('.KQ'):
        clean = clean[:6]

    # 1. Curated map first
    candidates = RELATED_MAP.get(clean, [])

    # 2. Sector-based fallback for any unlisted ticker
    if not candidates:
        sector     = _detect_sector(clean)
        candidates = SECTOR_POOL.get(sector, SECTOR_POOL["default"])

    results = []
    for c in candidates:
        r = _build_result(c, clean)
        if r:
            results.append(r)

    results.sort(key=lambda x: x['value_score'], reverse=True)
    return results[:5]
