"""
related_stocks.py — Supply-chain & sector-based related stock recommender.

Logic:
  1. Each major stock maps to a list of related tickers (supply chain, peers, enablers).
  2. For each related ticker, fetch basic fundamental metrics via yfinance:
       - Trailing P/E  (lower = cheaper)
       - Price/Book    (lower = undervalued)
       - Profit Margin (higher = more profitable)
       - Revenue Growth (positive = growing)
  3. Compute a simple Value Score (0–100) and return top candidates sorted by score.
  4. Falls back to curated static data if yfinance is rate-limited.
"""

import yfinance as yf
import numpy as np

# =========================================================================
#  Supply-Chain Relationship Map
#  Format: "TICKER": [ { ticker, name, relation, sector_tag } ]
# =========================================================================

RELATED_MAP: dict = {
    # ── SK하이닉스 (HBM / DRAM) ──────────────────────────────────────────
    "000660": [
        {"ticker": "042700", "name": "한미반도체", "relation": "HBM 패키징 핵심 장비 독점 공급사", "tag": "반도체 장비"},
        {"ticker": "240810", "name": "원익IPS",   "relation": "웨이퍼 증착/식각 공정 장비 1위", "tag": "반도체 장비"},
        {"ticker": "009150", "name": "삼성전기",  "relation": "패키지 기판 및 MLCC 핵심 부품 공급", "tag": "반도체 부품"},
        {"ticker": "357780", "name": "솔브레인",  "relation": "반도체 습식 식각액·세정 소재 공급", "tag": "반도체 소재"},
        {"ticker": "036830", "name": "솔브레인홀딩스", "relation": "솔브레인 지주사, 소재 사업 간접 노출", "tag": "반도체 소재"},
        {"ticker": "278280", "name": "천보",     "relation": "불화리튬 등 반도체·배터리 정밀 소재", "tag": "소재"},
    ],
    # ── 삼성전자 (파운드리 / DRAM / 스마트폰) ────────────────────────────
    "005930": [
        {"ticker": "042700", "name": "한미반도체",   "relation": "HBM TC-Bonder 독점 장비 공급사", "tag": "반도체 장비"},
        {"ticker": "009150", "name": "삼성전기",     "relation": "카메라 모듈·기판 삼성전자 직공급", "tag": "부품"},
        {"ticker": "012750", "name": "에스원",       "relation": "삼성그룹 계열 보안·시설관리", "tag": "서비스"},
        {"ticker": "005380", "name": "현대자동차",   "relation": "갤럭시-현대 커넥티드카 파트너십", "tag": "모빌리티"},
        {"ticker": "096770", "name": "SK이노베이션", "relation": "삼성SDI 경쟁사, 배터리 공급망 수혜", "tag": "배터리"},
        {"ticker": "357780", "name": "솔브레인",    "relation": "파운드리 공정 소재 공급사", "tag": "반도체 소재"},
    ],
    # ── 엔비디아 (NVDA) — GPU / AI 가속기 ──────────────────────────────
    "NVDA": [
        {"ticker": "TSM",  "name": "TSMC",          "relation": "NVDA GPU 독점 파운드리 제조사", "tag": "파운드리"},
        {"ticker": "AVGO", "name": "Broadcom",       "relation": "AI 네트워킹 칩 NVDA 공급망 수혜", "tag": "반도체"},
        {"ticker": "ANET", "name": "Arista Networks","relation": "AI 데이터센터 이더넷 인프라 공급", "tag": "네트워크"},
        {"ticker": "SMCI", "name": "Super Micro",    "relation": "NVDA GPU 서버 최대 OEM 파트너", "tag": "서버"},
        {"ticker": "AMD",  "name": "AMD",            "relation": "NVDA 대안 AI GPU 경쟁사 (가치투자)", "tag": "반도체"},
        {"ticker": "000660","name": "SK하이닉스",   "relation": "NVDA AI GPU용 HBM 독점 공급사", "tag": "메모리"},
    ],
    # ── 테슬라 (TSLA) ──────────────────────────────────────────────────
    "TSLA": [
        {"ticker": "373220", "name": "LG에너지솔루션","relation": "테슬라 원통형 배터리 주요 공급사", "tag": "배터리"},
        {"ticker": "PANAF", "name": "파나소닉",       "relation": "테슬라 기가팩토리 배터리 OEM 파트너", "tag": "배터리"},
        {"ticker": "ON",    "name": "onsemi",         "relation": "테슬라 SiC 전력반도체 공급사", "tag": "전력반도체"},
        {"ticker": "LEA",   "name": "Lear Corp",      "relation": "전기차 시트·전장 시스템 공급", "tag": "부품"},
        {"ticker": "005380","name": "현대자동차",    "relation": "테슬라 최대 경쟁사, 벨류에이션 비교", "tag": "완성차"},
    ],
    # ── LG에너지솔루션 (배터리 셀) ────────────────────────────────────
    "373220": [
        {"ticker": "247540", "name": "에코프로비엠", "relation": "하이니켈 양극재 독점 공급사", "tag": "양극재"},
        {"ticker": "302440", "name": "SK아이이테크놀로지","relation": "분리막 공급사 (배터리 핵심)", "tag": "분리막"},
        {"ticker": "278280", "name": "천보",         "relation": "전해질 LiFSI 공급사", "tag": "소재"},
        {"ticker": "006400", "name": "삼성SDI",      "relation": "배터리 셀 경쟁사, 상대가치 비교", "tag": "배터리"},
        {"ticker": "005490", "name": "POSCO홀딩스", "relation": "리튬·니켈 소재 공급 및 양극재 계열사", "tag": "소재"},
    ],
    # ── 한화에어로스페이스 (방산) ──────────────────────────────────────
    "012450": [
        {"ticker": "047810", "name": "한국항공우주(KAI)", "relation": "KF-21 전투기 공동개발사", "tag": "방산"},
        {"ticker": "000970", "name": "한화",          "relation": "한화에어로 대주주 지주사", "tag": "지주"},
        {"ticker": "064350", "name": "현대로템",      "relation": "K2 전차·철도 방산 동반 수출 기대", "tag": "방산"},
        {"ticker": "272210", "name": "한화시스템",    "relation": "전자전·레이더 방산 계열사", "tag": "방산"},
        {"ticker": "LMT",   "name": "Lockheed Martin","relation": "글로벌 방산 벤치마크 대형주", "tag": "방산"},
    ],
    # ── 삼성바이오로직스 (CMO 바이오) ─────────────────────────────────
    "207940": [
        {"ticker": "068270", "name": "셀트리온",     "relation": "바이오시밀러 경쟁·협력 관계", "tag": "바이오"},
        {"ticker": "128940", "name": "한미약품",     "relation": "글로벌 기술수출 선두 신약개발사", "tag": "제약"},
        {"ticker": "000100", "name": "유한양행",     "relation": "레이저티닙 FDA 허가, 신약 파이프라인", "tag": "제약"},
        {"ticker": "196170", "name": "알테오젠",     "relation": "SC플랫폼 기술수출 바이오 선두주", "tag": "바이오"},
    ],
    # ── 현대자동차 ─────────────────────────────────────────────────────
    "005380": [
        {"ticker": "012330", "name": "현대모비스",   "relation": "현대차 핵심 부품 1차 벤더", "tag": "부품"},
        {"ticker": "011210", "name": "현대위아",     "relation": "엔진·모듈·방산 현대차 계열사", "tag": "부품"},
        {"ticker": "161390", "name": "한국타이어앤테크놀로지","relation": "완성차 OE 타이어 공급사", "tag": "부품"},
        {"ticker": "002700", "name": "기아",         "relation": "현대차 동생사, 고마진 PBV 사업", "tag": "완성차"},
        {"ticker": "TSLA",  "name": "Tesla",         "relation": "EV 시장 직접 경쟁사 (벨류에이션)", "tag": "EV"},
    ],
    # ── 알테오젠 ──────────────────────────────────────────────────────
    "196170": [
        {"ticker": "207940", "name": "삼성바이오로직스","relation": "CMO 바이오 플랫폼 선두사", "tag": "바이오"},
        {"ticker": "000100", "name": "유한양행",     "relation": "레이저티닙 공동개발, 신약 파이프라인", "tag": "제약"},
        {"ticker": "128940", "name": "한미약품",     "relation": "글로벌 기술수출 동반 성장주", "tag": "제약"},
    ],
    # ── AMD ────────────────────────────────────────────────────────────
    "AMD": [
        {"ticker": "NVDA",  "name": "Nvidia",         "relation": "AI GPU 직접 경쟁사 (시장 주도)", "tag": "반도체"},
        {"ticker": "TSM",   "name": "TSMC",           "relation": "AMD CPU/GPU 독점 파운드리 제조", "tag": "파운드리"},
        {"ticker": "INTC",  "name": "Intel",          "relation": "x86 CPU 전통 경쟁사 (회복 여부 주시)", "tag": "반도체"},
        {"ticker": "MU",    "name": "Micron",         "relation": "AI 서버 메모리 공급망 수혜", "tag": "메모리"},
    ],
}

# Fallback curated fundamental data (approximate, updated periodically)
# Used when yfinance rate-limits or fails
STATIC_FUNDAMENTALS: dict = {
    "042700": {"pe": 28.5,  "pb": 6.2,  "margin": 22.1, "growth": 45.2},
    "240810": {"pe": 18.3,  "pb": 2.8,  "margin": 12.4, "growth": 18.5},
    "009150": {"pe": 14.2,  "pb": 1.8,  "margin": 8.3,  "growth": 9.1},
    "357780": {"pe": 22.1,  "pb": 3.5,  "margin": 18.7, "growth": 22.3},
    "005380": {"pe": 6.8,   "pb": 0.72, "margin": 9.2,  "growth": 7.5},
    "012330": {"pe": 8.5,   "pb": 0.88, "margin": 7.1,  "growth": 5.2},
    "002700": {"pe": 5.9,   "pb": 0.65, "margin": 11.3, "growth": 8.8},
    "373220": {"pe": 42.1,  "pb": 3.2,  "margin": 6.8,  "growth": 28.4},
    "006400": {"pe": 31.5,  "pb": 1.9,  "margin": 5.2,  "growth": 15.6},
    "247540": {"pe": 35.2,  "pb": 5.8,  "margin": 15.2, "growth": 35.1},
    "207940": {"pe": 55.3,  "pb": 7.1,  "margin": 24.8, "growth": 32.5},
    "068270": {"pe": 28.4,  "pb": 2.9,  "margin": 18.2, "growth": 22.0},
    "128940": {"pe": 85.0,  "pb": 9.2,  "margin": 12.1, "growth": 41.5},
    "000100": {"pe": 32.1,  "pb": 3.1,  "margin": 10.5, "growth": 28.0},
    "196170": {"pe": 120.0, "pb": 15.3, "margin": 38.5, "growth": 85.2},
    "012450": {"pe": 22.8,  "pb": 3.4,  "margin": 8.9,  "growth": 55.2},
    "047810": {"pe": 18.5,  "pb": 1.9,  "margin": 6.8,  "growth": 38.4},
    "064350": {"pe": 25.2,  "pb": 2.1,  "margin": 5.5,  "growth": 42.0},
    "272210": {"pe": 35.1,  "pb": 4.2,  "margin": 10.2, "growth": 30.5},
    "005490": {"pe": 15.2,  "pb": 0.95, "margin": 12.8, "growth": 18.5},
    "278280": {"pe": 28.5,  "pb": 4.1,  "margin": 20.3, "growth": 25.0},
    "302440": {"pe": 38.5,  "pb": 5.2,  "margin": 14.5, "growth": 20.5},
    "011210": {"pe": 10.5,  "pb": 0.82, "margin": 6.2,  "growth": 8.5},
    "161390": {"pe": 12.8,  "pb": 1.1,  "margin": 9.5,  "growth": 6.2},
    "096770": {"pe": 8.5,   "pb": 0.65, "margin": 7.8,  "growth": 12.5},
    "000970": {"pe": 18.5,  "pb": 1.2,  "margin": 4.5,  "growth": 25.0},
    "000660": {"pe": 18.5,  "pb": 1.95, "margin": 21.5, "growth": 42.0},
    "005930": {"pe": 15.2,  "pb": 1.55, "margin": 12.5, "growth": 8.5},
    # US Stocks
    "TSM":   {"pe": 22.1,  "pb": 6.8,  "margin": 38.2, "growth": 28.5},
    "AVGO":  {"pe": 28.5,  "pb": 9.5,  "margin": 52.1, "growth": 42.0},
    "ANET":  {"pe": 38.5,  "pb": 14.2, "margin": 30.5, "growth": 22.5},
    "SMCI":  {"pe": 15.5,  "pb": 3.2,  "margin": 8.5,  "growth": 85.5},
    "AMD":   {"pe": 42.5,  "pb": 4.2,  "margin": 10.5, "growth": 18.5},
    "ON":    {"pe": 22.5,  "pb": 4.5,  "margin": 28.5, "growth": 8.5},
    "LEA":   {"pe": 10.5,  "pb": 1.1,  "margin": 5.2,  "growth": 8.5},
    "LMT":   {"pe": 18.5,  "pb": 12.5, "margin": 9.5,  "growth": 5.5},
    "MU":    {"pe": 12.5,  "pb": 2.2,  "margin": 15.5, "growth": 52.5},
    "INTC":  {"pe": 28.5,  "pb": 1.5,  "margin": 2.5,  "growth": -5.5},
    "NVDA":  {"pe": 45.5,  "pb": 25.5, "margin": 55.5, "growth": 122.0},
    "TSLA":  {"pe": 75.5,  "pb": 8.5,  "margin": 8.5,  "growth": 2.5},
}


def _value_score(pe: float, pb: float, margin: float, growth: float) -> float:
    """Compute a 0-100 Value Score combining undervaluation + profitability.
    
    Higher score = better value (cheap + profitable + growing).
    
    Scoring weights:
        - P/E score (30%):     lower P/E → higher score; ideal range 10-25
        - P/B score (20%):     lower P/B → higher score; ideal range 0.5-3
        - Profit margin (30%): higher margin → higher score
        - Growth (20%):        higher revenue growth → higher score
    """
    # P/E score: best at PE=15, penalise very high (>60) or negative
    if pe <= 0 or pe > 200:
        pe_score = 0.0
    else:
        pe_score = max(0, 100 - abs(pe - 15) * 2)
        pe_score = min(pe_score, 100)

    # P/B score: best at PB=1-1.5
    if pb <= 0:
        pb_score = 0.0
    else:
        pb_score = max(0, 100 - abs(pb - 1.5) * 15)
        pb_score = min(pb_score, 100)

    # Margin score: 0% → 0, 50%+ → 100
    margin_score = min(max(margin * 2, 0), 100)

    # Growth score: 0% → 50 base, positive = better, negative penalised
    growth_score = min(max(50 + growth * 0.8, 0), 100)

    score = (pe_score * 0.30) + (pb_score * 0.20) + (margin_score * 0.30) + (growth_score * 0.20)
    return round(float(score), 1)


def _fetch_fundamentals(ticker: str) -> dict:
    """Try to fetch live fundamentals from yfinance; fall back to static data."""
    # Try yfinance first
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info or {}
        pe    = float(info.get('trailingPE') or info.get('forwardPE') or 0)
        pb    = float(info.get('priceToBook') or 0)
        margin= float(info.get('profitMargins') or 0) * 100  # yfinance returns decimal
        growth= float(info.get('revenueGrowth') or 0) * 100

        if pe > 0 or pb > 0:  # At least one metric retrieved
            return {"pe": round(pe, 1), "pb": round(pb, 2), "margin": round(margin, 1), "growth": round(growth, 1), "source": "live"}
    except Exception:
        pass

    # Fall back to static curated data
    static = STATIC_FUNDAMENTALS.get(ticker.upper(), {})
    if static:
        return {**static, "source": "curated"}

    return {"pe": 0, "pb": 0, "margin": 0, "growth": 0, "source": "unknown"}


def get_related_stocks(ticker: str) -> list:
    """Return scored related stock recommendations for a given ticker.
    
    Args:
        ticker: Primary stock ticker (e.g. '000660', 'NVDA')
    
    Returns:
        List of related stocks, sorted by value_score descending.
        Each item:
            ticker, name, relation, tag, pe, pb, margin, growth,
            value_score, value_grade, data_source
    """
    clean = ticker.upper().strip()

    # Normalise Korean 6-digit codes that arrive with exchange suffix
    if clean.endswith('.KS') or clean.endswith('.KQ'):
        clean = clean[:6]

    candidates = RELATED_MAP.get(clean, [])
    if not candidates:
        return []

    results = []
    for candidate in candidates:
        t  = candidate['ticker']
        fd = _fetch_fundamentals(t)

        score = _value_score(
            fd['pe'], fd['pb'], fd['margin'], fd['growth']
        )

        # Value grade label
        if score >= 70:
            value_grade = "💎 고가치"
            grade_color = "emerald"
        elif score >= 50:
            value_grade = "📊 적정"
            grade_color = "amber"
        else:
            value_grade = "⚠️ 고평가"
            grade_color = "red"

        # Investment rationale summary
        highlights = []
        if fd['margin'] >= 20:
            highlights.append(f"고수익성 (영업이익률 {fd['margin']}%)")
        if fd['pb'] > 0 and fd['pb'] < 2.0:
            highlights.append(f"저PBR {fd['pb']} (자산 대비 저평가)")
        if fd['pe'] > 0 and fd['pe'] < 20:
            highlights.append(f"저PER {fd['pe']} (이익 대비 저평가)")
        if fd['growth'] >= 20:
            highlights.append(f"매출 고성장 +{fd['growth']}%")
        if not highlights:
            highlights.append("시장 연관도 높은 공급망 수혜주")

        results.append({
            "ticker":      t,
            "name":        candidate['name'],
            "relation":    candidate['relation'],
            "tag":         candidate['tag'],
            "pe":          fd['pe'],
            "pb":          fd['pb'],
            "margin":      fd['margin'],
            "growth":      fd['growth'],
            "value_score": score,
            "value_grade": value_grade,
            "grade_color": grade_color,
            "highlights":  highlights,
            "data_source": fd['source']
        })

    # Sort by value_score descending; return top 5
    results.sort(key=lambda x: x['value_score'], reverse=True)
    return results[:5]


if __name__ == '__main__':
    print("=== Related Stocks Test (SK하이닉스 000660) ===")
    for r in get_related_stocks('000660'):
        print(f"  [{r['value_grade']}] {r['name']} ({r['ticker']}) — Score: {r['value_score']}")
        print(f"    PE={r['pe']} | PB={r['pb']} | Margin={r['margin']}% | Growth={r['growth']}%")
        print(f"    ↳ {r['highlights']}")
    print("\n=== Related Stocks Test (NVDA) ===")
    for r in get_related_stocks('NVDA'):
        print(f"  [{r['value_grade']}] {r['name']} ({r['ticker']}) — Score: {r['value_score']}")
