import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import datetime
import numpy as np

# =========================================================================
#  Financial Sentiment Keywords (Korean + English)
# =========================================================================

KO_POS = ['상승', '호재', '상회', '흑자', '최고', '대박', '인수', '계약', '돌파',
          '성장', '출시', '개발', '성공', '급등', '호조', '안정', '이익', '증가',
          '배당', '추천', '강세', '전망', '급증', '수주', '수출', '매출']

KO_NEG = ['하락', '악재', '하회', '적자', '최저', '소송', '리콜', '감소', '급락',
          '우려', '손실', '분쟁', '제재', '부진', '충격', '쇼크', '위기', '경고',
          '규제', '악화', '약세', '축소', '급감', '폭락', '파산', '취소']

# 부정어 리스트: 이 단어 뒤에 긍정 키워드가 오면 부정으로 전환
KO_NEGATION = ['않', '안', '못', '없', '아니', '불가', '미달', '미흡', '실패', '부재']

EN_POS = ['surge', 'jump', 'gain', 'rise', 'beat', 'growth', 'bullish', 'upgrade',
          'success', 'expand', 'highest', 'profit', 'dividend', 'deal', 'buy',
          'outperform', 'strong', 'acquisition', 'innovative', 'positive', 'record']

EN_NEG = ['drop', 'fall', 'plunge', 'loss', 'sink', 'bearish', 'downgrade', 'failure',
          'shrink', 'lowest', 'deficit', 'sue', 'lawsuit', 'recall', 'decline', 'weak',
          'risk', 'crisis', 'layoff', 'warn', 'negative', 'slump', 'tumble']

EN_NEGATION = ['not', "n't", 'no', 'never', 'fail', 'miss', 'below', 'under']


def analyze_sentiment(text, is_korean=True):
    """Classifies a headline as Positive, Negative, or Neutral.
    
    Improvements vs v1:
    - Korean negation detection (부정어 처리)
    - Keyword density scoring instead of raw count
    - Context window: negation within 3 characters/words flips sentiment
    """
    text_lower = text.lower()
    pos_score = 0.0
    neg_score = 0.0

    if is_korean:
        # --- Korean: character-level negation window (±5 chars) ---
        for kw in KO_POS:
            idx = text_lower.find(kw)
            while idx != -1:
                window = text_lower[max(0, idx - 5): idx]
                # Check if a negation word precedes this positive keyword
                negated = any(neg in window for neg in KO_NEGATION)
                if negated:
                    neg_score += 0.8   # negated positive → treat as negative
                else:
                    pos_score += 1.0
                idx = text_lower.find(kw, idx + 1)

        for kw in KO_NEG:
            if kw in text_lower:
                neg_score += 1.0

    else:
        # --- English: word-level negation window (±2 words) ---
        words = re.split(r'\W+', text_lower)
        for i, word in enumerate(words):
            if word in EN_POS:
                window_start = max(0, i - 2)
                preceding = words[window_start:i]
                negated = any(neg in preceding for neg in EN_NEGATION)
                if negated:
                    neg_score += 0.8
                else:
                    pos_score += 1.0
            if word in EN_NEG:
                neg_score += 1.0

    # Density normalization: longer titles should not automatically score higher
    word_count = max(len(text.split()), 1)
    pos_density = pos_score / word_count
    neg_density = neg_score / word_count

    # Classify: require at least a minimum density gap to avoid neutral misclassification
    if pos_score > neg_score and pos_density > 0.02:
        return 'Positive'
    elif neg_score > pos_score and neg_density > 0.02:
        return 'Negative'
    else:
        return 'Neutral'


def get_naver_news(code):
    """Crawls recent news headlines from Naver Finance for a given Korean stock code.
    
    Returns items with `is_simulated=False` when real data is available.
    Falls back to clearly-flagged simulated news if crawling fails.
    """
    clean_code = re.sub(r'\D', '', code)
    if not clean_code:
        return []

    url = f"https://finance.naver.com/item/news_news.naver?code={clean_code}"
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'),
        'Referer': f'https://finance.naver.com/item/main.naver?code={clean_code}'
    }

    news_list = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        anchors = soup.find_all('a')
        added_links = set()

        for a in anchors:
            href = a.get('href', '')
            if href and 'news_read.naver' in href:
                title_text = a.get_text().strip()
                if not title_text or len(title_text) < 4:
                    continue

                full_link = f"https://finance.naver.com{href}" if href.startswith('/') else href
                if full_link in added_links:
                    continue
                added_links.add(full_link)

                source_text = "네이버 금융"
                date_text = datetime.datetime.now().strftime('%Y-%m-%d')

                try:
                    parent_td = a.find_parent('td')
                    if parent_td:
                        parent_tr = parent_td.find_parent('tr')
                        if parent_tr:
                            info_td = parent_tr.find('td', class_='info')
                            if info_td:
                                source_text = info_td.get_text().strip()
                            date_td = parent_tr.find('td', class_='date')
                            if date_td:
                                date_text = date_td.get_text().strip()
                except Exception:
                    pass

                sentiment = analyze_sentiment(title_text, is_korean=True)

                news_list.append({
                    'title': title_text,
                    'link': full_link,
                    'source': source_text,
                    'date': date_text,
                    'sentiment': sentiment,
                    'is_simulated': False   # ← Real data flag
                })

                if len(news_list) >= 15:
                    break

    except Exception as e:
        print(f"Error crawling Naver news for code {code}: {e}")

    # Self-healing: clearly flagged simulated fallback
    if not news_list:
        print(f"[Self-Healing] Naver news empty for {code}. Using flagged simulated news.")
        mock_headlines = [
            (f"[특징주] {code} 장중 기관 수급 유입... 주가 반등 시도", '한국경제'),
            (f"{code} 외인 순매수 지속... 증권가 목표주가 상향 잇따라", '매일경제'),
            (f"[공시] {code} 2분기 실적 전망치 상회 가능성", '연합인포맥스'),
            (f"{code} 원자재 가격 상승 여파로 단기 마진 압박 우려", '머니투데이'),
            (f"주식 시장 진단: {code} 밸류에이션 매력도 점검", '아시아경제')
        ]
        for i, (title, src) in enumerate(mock_headlines):
            d = datetime.datetime.now() - datetime.timedelta(hours=i * 2)
            news_list.append({
                'title': title,
                'link': 'https://finance.naver.com/',
                'source': src,
                'date': d.strftime('%Y-%m-%d %H:%M'),
                'sentiment': analyze_sentiment(title, is_korean=True),
                'is_simulated': True    # ← Simulated data flag
            })

    return news_list


def get_us_news(ticker):
    """Fetches recent news from Yahoo Finance for a US stock ticker.
    
    Returns items with `is_simulated=False` when real data is available.
    Falls back to clearly-flagged simulated news if rate-limited.
    """
    news_list = []
    try:
        stock = yf.Ticker(ticker)
        yf_news = stock.news

        if yf_news and isinstance(yf_news, list):
            for item in yf_news[:15]:
                title_text = item.get('title', '').strip()
                link = item.get('link', '')

                if not title_text or not link:
                    continue

                publisher = item.get('publisher', 'Yahoo Finance')
                provider_pub_time = item.get('providerPublishTime', 0)

                if provider_pub_time > 0:
                    dt = datetime.datetime.fromtimestamp(provider_pub_time)
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

                sentiment = analyze_sentiment(title_text, is_korean=False)

                news_list.append({
                    'title': title_text,
                    'link': link,
                    'source': publisher,
                    'date': date_str,
                    'sentiment': sentiment,
                    'is_simulated': False   # ← Real data flag
                })
    except Exception as e:
        print(f"Error fetching US news for ticker {ticker}: {e}")

    # Self-healing: clearly flagged simulated fallback
    if not news_list:
        print(f"[Self-Healing] US news empty for {ticker}. Using flagged simulated news.")
        mock_headlines = [
            (f"{ticker} Reports Mixed Q2 Results Amid Macro Headwinds", 'Reuters'),
            (f"Analysts Divided on {ticker} Outlook After Earnings Release", 'Bloomberg'),
            (f"{ticker} Faces Regulatory Scrutiny in Key Markets", 'WSJ'),
            (f"Institutional Investors Increase {ticker} Holdings", 'MarketWatch'),
            (f"{ticker} Product Launch Sparks Debate Among Analysts", 'CNBC')
        ]
        for i, (title, src) in enumerate(mock_headlines):
            d = datetime.datetime.now() - datetime.timedelta(hours=i * 3)
            news_list.append({
                'title': title,
                'link': 'https://finance.yahoo.com/',
                'source': src,
                'date': d.strftime('%Y-%m-%d %H:%M'),
                'sentiment': analyze_sentiment(title, is_korean=False),
                'is_simulated': True    # ← Simulated data flag
            })

    return news_list


if __name__ == '__main__':
    print("Testing Naver news crawler (005930):")
    results = get_naver_news('005930')
    for r in results[:3]:
        print(f"  [{r['sentiment']}] {'[SIM]' if r['is_simulated'] else '[LIVE]'} {r['title']}")
    print("\nTesting US news (TSLA):")
    results = get_us_news('TSLA')
    for r in results[:3]:
        print(f"  [{r['sentiment']}] {'[SIM]' if r['is_simulated'] else '[LIVE]'} {r['title']}")
