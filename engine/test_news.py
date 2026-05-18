import requests
from bs4 import BeautifulSoup
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/item/main.naver?code=005930'
}
url = "https://finance.naver.com/item/news_news.naver?code=005930"
res = requests.get(url, headers=headers)
res.encoding = 'euc-kr'
soup = BeautifulSoup(res.text, 'html.parser')

print("All anchor tags with Referer provided:")
for a in soup.find_all('a'):
    href = a.get('href')
    if href and 'news_read' in href:
        print(a.get_text().strip(), href)
