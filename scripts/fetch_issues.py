#!/usr/bin/env python3
"""
한국-미국 기업 이슈 뉴스 수집 + AI 요약 스크립트 v1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
섹터 15개 × 한미 기업 크로스 이슈 자동 수집
RSS / Yahoo Finance News / 구글 뉴스 RSS 활용
"""

import json, os, time, re
from datetime import datetime, timedelta
import pytz
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

KST = pytz.timezone('Asia/Seoul')
NOW = datetime.now(KST)

# ─── 섹터 정의 (15개) ─────────────────────────────────────────
SECTORS = [
    {
        "id": "semiconductor",
        "name": "반도체",
        "icon": "💾",
        "color": "blue",
        "kr_keywords": ["삼성전자", "SK하이닉스", "한미반도체", "주성엔지니어링", "원익IPS"],
        "us_keywords": ["NVIDIA", "Intel", "TSMC", "Qualcomm", "AMD", "Micron"],
        "search_terms": ["반도체 HBM AI", "semiconductor chip AI demand", "NVIDIA 삼성 협력"],
        "kr_stocks": ["005930","000660","042700","036930","240810"],
        "us_stocks": ["NVDA","INTC","TSM","QCOM","AMD"],
    },
    {
        "id": "robot",
        "name": "로봇·자동화",
        "icon": "🤖",
        "color": "purple",
        "kr_keywords": ["현대로보틱스", "레인보우로보틱스", "두산로보틱스", "HD현대", "현대차 로봇"],
        "us_keywords": ["Boston Dynamics", "Tesla Optimus", "Figure AI", "ABB", "Rockwell"],
        "search_terms": ["한국 로봇 상한가", "humanoid robot Korea", "현대 보스턴다이나믹스"],
        "kr_stocks": ["285490","464850","243570","267270","005380"],
        "us_stocks": ["TER","ROK","ISRG","IRBT","FANUY"],
    },
    {
        "id": "ai_sw",
        "name": "AI·소프트웨어",
        "icon": "🧠",
        "color": "cyan",
        "kr_keywords": ["NAVER", "카카오", "SKT AI", "KT AI", "솔트룩스"],
        "us_keywords": ["OpenAI", "Microsoft", "Google", "Meta AI", "Anthropic"],
        "search_terms": ["한국 AI 소프트웨어", "AI software Korea", "LLM 한국어"],
        "kr_stocks": ["035420","035720","017670","030200","376300"],
        "us_stocks": ["MSFT","GOOGL","META","CRM","NOW"],
    },
    {
        "id": "ev_battery",
        "name": "전기차·배터리",
        "icon": "🔋",
        "color": "green",
        "kr_keywords": ["LG에너지솔루션", "삼성SDI", "에코프로", "포스코퓨처엠", "현대차 전기차"],
        "us_keywords": ["Tesla", "GM EV", "Ford EV", "Rivian", "Panasonic battery"],
        "search_terms": ["배터리 전기차 수주", "EV battery Korea contract", "IRA 보조금"],
        "kr_stocks": ["373220","006400","086520","003670","005380"],
        "us_stocks": ["TSLA","GM","F","RIVN","PCRFY"],
    },
    {
        "id": "defense",
        "name": "방산·항공우주",
        "icon": "🚀",
        "color": "orange",
        "kr_keywords": ["한화에어로스페이스", "한국항공우주", "현대로템", "한화시스템", "LIG넥스원"],
        "us_keywords": ["Lockheed Martin", "Raytheon", "Northrop", "Boeing Defense", "L3Harris"],
        "search_terms": ["K방산 수출", "Korean defense export", "FA-50 K2 수출"],
        "kr_stocks": ["012450","047810","064350","272210","079550"],
        "us_stocks": ["LMT","RTX","NOC","BA","LHX"],
    },
    {
        "id": "shipbuilding",
        "name": "조선·해양",
        "icon": "🚢",
        "color": "teal",
        "kr_keywords": ["HD한국조선해양", "삼성중공업", "한화오션", "HMM", "HD현대중공업"],
        "us_keywords": ["LNG carrier", "containership order", "shipping freight"],
        "search_terms": ["LNG선 수주 한국", "조선 수주 잔량", "Korean shipbuilding order"],
        "kr_stocks": ["009540","010140","042660","011200","267270"],
        "us_stocks": ["MATX","ZIM","DAC","SBLK","GSL"],
    },
    {
        "id": "bio_pharma",
        "name": "바이오·제약",
        "icon": "🧬",
        "color": "pink",
        "kr_keywords": ["삼성바이오로직스", "셀트리온", "한미약품", "유한양행", "알테오젠"],
        "us_keywords": ["Novo Nordisk", "Eli Lilly", "Pfizer", "AstraZeneca", "Moderna"],
        "search_terms": ["바이오시밀러 FDA", "GLP-1 비만 한국", "Korean biotech license"],
        "kr_stocks": ["207940","068270","128940","000100","196170"],
        "us_stocks": ["NVO","LLY","PFE","AZN","MRNA"],
    },
    {
        "id": "clean_energy",
        "name": "클린에너지·원전",
        "icon": "☀️",
        "color": "yellow",
        "kr_keywords": ["한화솔루션", "두산에너빌리티", "한국전력", "LS ELECTRIC", "씨에스윈드"],
        "us_keywords": ["First Solar", "Constellation Energy", "Bloom Energy", "NextEra"],
        "search_terms": ["원전 수출 한국", "태양광 IRA", "nuclear SMR Korea"],
        "kr_stocks": ["009830","034020","015760","010120","112610"],
        "us_stocks": ["FSLR","CEG","BE","NEE","ENPH"],
    },
    {
        "id": "finance",
        "name": "금융·핀테크",
        "icon": "🏦",
        "color": "gold",
        "kr_keywords": ["KB금융", "신한지주", "카카오페이", "토스", "삼성증권"],
        "us_keywords": ["JPMorgan", "Goldman Sachs", "BlackRock", "Visa", "Mastercard"],
        "search_terms": ["한국 금융 금리", "Korea fintech IPO", "카카오페이 토스 해외"],
        "kr_stocks": ["105560","055550","377300","016360","071050"],
        "us_stocks": ["JPM","GS","BLK","V","MA"],
    },
    {
        "id": "display",
        "name": "디스플레이·부품",
        "icon": "📺",
        "color": "indigo",
        "kr_keywords": ["LG디스플레이", "삼성디스플레이", "덕산네오룩스", "이녹스첨단소재"],
        "us_keywords": ["Apple display", "OLED demand", "Meta Quest display", "Vision Pro"],
        "search_terms": ["OLED 수주 애플", "한국 디스플레이 OLED", "Apple Korea display"],
        "kr_stocks": ["034220","213420","078600","272290"],
        "us_stocks": ["AAPL","META","GOOGL","SNE"],
    },
    {
        "id": "consumer",
        "name": "소비재·K브랜드",
        "icon": "🛍️",
        "color": "rose",
        "kr_keywords": ["현대차", "기아", "아모레퍼시픽", "LG생활건강", "오리온"],
        "us_keywords": ["Amazon", "Walmart", "Costco", "Target", "K-beauty trend"],
        "search_terms": ["K뷰티 미국 수출", "현대차 미국 판매", "Korean brand US market"],
        "kr_stocks": ["005380","000270","090430","051900","271560"],
        "us_stocks": ["AMZN","WMT","COST","TGT","HD"],
    },
    {
        "id": "telecom_media",
        "name": "통신·콘텐츠",
        "icon": "📡",
        "color": "violet",
        "kr_keywords": ["SK텔레콤", "KT", "하이브", "에스엠", "카카오엔터"],
        "us_keywords": ["Netflix", "Spotify", "YouTube", "Disney", "K-pop global"],
        "search_terms": ["K팝 넷플릭스 글로벌", "한국 콘텐츠 수출", "Kpop Kdrema streaming"],
        "kr_stocks": ["017670","030200","352820","041510","035900"],
        "us_stocks": ["NFLX","SPOT","GOOGL","DIS","WBD"],
    },
    {
        "id": "steel_material",
        "name": "철강·소재",
        "icon": "⚙️",
        "color": "slate",
        "kr_keywords": ["POSCO홀딩스", "현대제철", "고려아연", "포스코퓨처엠"],
        "us_keywords": ["US Steel", "Nucor", "Freeport McMoRan", "Albemarle", "Lithium"],
        "search_terms": ["철강 관세 한국", "리튬 공급망 한국", "Korean steel tariff US"],
        "kr_stocks": ["005490","004020","010130","003670"],
        "us_stocks": ["X","NUE","FCX","ALB","MP"],
    },
    {
        "id": "logistics",
        "name": "물류·이커머스",
        "icon": "📦",
        "color": "amber",
        "kr_keywords": ["CJ대한통운", "한진", "쿠팡", "HMM", "롯데글로벌로지스"],
        "us_keywords": ["Amazon Logistics", "FedEx", "UPS", "Maersk", "DHL"],
        "search_terms": ["쿠팡 미국 진출", "한국 물류 이커머스", "Korea logistics US"],
        "kr_stocks": ["000120","002320","003160","011200","086280"],
        "us_stocks": ["AMZN","FDX","UPS","CHRW","XPO"],
    },
    {
        "id": "construction",
        "name": "건설·인프라",
        "icon": "🏗️",
        "color": "stone",
        "kr_keywords": ["현대건설", "삼성물산", "GS건설", "대우건설", "한화건설"],
        "us_keywords": ["Bechtel", "Fluor", "infrastructure bill", "data center construction"],
        "search_terms": ["해외 건설 수주 한국", "데이터센터 건설 한국", "Korean construction overseas"],
        "kr_stocks": ["000720","028260","006360","047040","009830"],
        "us_stocks": ["FLR","ACM","PWR","STRL","EME"],
    },
]

# ─── 색상 매핑 ────────────────────────────────────────────────
COLOR_MAP = {
    "blue":   {"bg": "rgba(99,179,237,.08)",  "border": "rgba(99,179,237,.25)",  "text": "#63b3ed"},
    "purple": {"bg": "rgba(168,85,247,.08)",  "border": "rgba(168,85,247,.25)",  "text": "#a855f7"},
    "cyan":   {"bg": "rgba(79,209,197,.08)",  "border": "rgba(79,209,197,.25)",  "text": "#4fd1c5"},
    "green":  {"bg": "rgba(38,222,129,.08)",  "border": "rgba(38,222,129,.25)",  "text": "#26de81"},
    "orange": {"bg": "rgba(255,107,53,.08)",  "border": "rgba(255,107,53,.25)",  "text": "#ff6b35"},
    "teal":   {"bg": "rgba(45,212,191,.08)",  "border": "rgba(45,212,191,.25)",  "text": "#2dd4bf"},
    "pink":   {"bg": "rgba(244,114,182,.08)", "border": "rgba(244,114,182,.25)", "text": "#f472b6"},
    "yellow": {"bg": "rgba(251,191,36,.08)",  "border": "rgba(251,191,36,.25)",  "text": "#fbbf24"},
    "gold":   {"bg": "rgba(246,201,14,.08)",  "border": "rgba(246,201,14,.25)",  "text": "#f6c90e"},
    "indigo": {"bg": "rgba(99,102,241,.08)",  "border": "rgba(99,102,241,.25)",  "text": "#6366f1"},
    "rose":   {"bg": "rgba(251,113,133,.08)", "border": "rgba(251,113,133,.25)", "text": "#fb7185"},
    "violet": {"bg": "rgba(139,92,246,.08)",  "border": "rgba(139,92,246,.25)",  "text": "#8b5cf6"},
    "slate":  {"bg": "rgba(148,163,184,.08)", "border": "rgba(148,163,184,.25)", "text": "#94a3b8"},
    "amber":  {"bg": "rgba(251,146,60,.08)",  "border": "rgba(251,146,60,.25)",  "text": "#fb923c"},
    "stone":  {"bg": "rgba(168,162,158,.08)", "border": "rgba(168,162,158,.25)", "text": "#a8a29e"},
}

# ─── 뉴스 수집 함수 ───────────────────────────────────────────
def fetch_google_rss(query, max_items=3):
    """구글 뉴스 RSS로 뉴스 수집"""
    items = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read().decode('utf-8', errors='ignore')

        root = ET.fromstring(xml_data)
        channel = root.find('channel')
        if channel is None:
            return items

        for item in channel.findall('item')[:max_items]:
            title = item.findtext('title', '').strip()
            link  = item.findtext('link', '').strip()
            pub   = item.findtext('pubDate', '').strip()
            src_el = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            source = item.findtext('source', '')

            # 날짜 파싱
            pub_str = ''
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub)
                kst_dt = dt.astimezone(KST)
                pub_str = kst_dt.strftime('%m/%d %H:%M')
            except:
                pub_str = pub[:16] if pub else ''

            # 제목 정제
            title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()  # 출처 제거
            if title and len(title) > 10:
                items.append({
                    "title": title,
                    "link":  link,
                    "pub":   pub_str,
                    "source": source if isinstance(source, str) else '',
                })
    except Exception as e:
        print(f"    RSS 오류: {e}")
    return items


def classify_sentiment(title):
    """제목 기반 감성 분류"""
    pos_kw = ['상한가', '급등', '수주', '호실적', '협력', '계약', '진출', '수출',
              '성장', '확대', '신제품', '투자', '승인', '허가', '돌파', '최고', '선정',
              'surge', 'gain', 'rise', 'record', 'deal', 'contract', 'expand', 'approve']
    neg_kw = ['하한가', '급락', '취소', '손실', '제재', '규제', '우려', '위기',
              '감소', '축소', '실망', '경고', '조사', '소송', '지연', '적자',
              'drop', 'fall', 'loss', 'sanction', 'delay', 'concern', 'risk', 'recall']

    title_l = title.lower()
    pos_score = sum(1 for k in pos_kw if k in title_l)
    neg_score = sum(1 for k in neg_kw if k in title_l)

    if pos_score > neg_score:   return "positive"
    elif neg_score > pos_score: return "negative"
    else:                       return "neutral"


def impact_score(title, sector):
    """이슈 임팩트 점수 (1~5)"""
    high_kw = ['상한가', '하한가', '계약', '수주', '협력', '투자', 'deal', 'contract', 'surge', 'plunge']
    mid_kw  = ['호실적', '부진', '확대', '축소', 'record', 'miss', 'expand']
    title_l = title.lower()
    if any(k in title_l for k in high_kw): return 5
    if any(k in title_l for k in mid_kw):  return 3
    return 2


# ─── 메인 ────────────────────────────────────────────────────
def main():
    print("=" * 62)
    print("📰 한국-미국 기업 이슈 뉴스 수집 시작")
    print(f"   수집 시각: {NOW.strftime('%Y-%m-%d %H:%M KST')}")
    print("=" * 62)

    all_issues = []

    for sec in SECTORS:
        print(f"\n  {sec['icon']} [{sec['name']}] 수집 중...")
        sector_issues = []
        seen_titles = set()

        # 검색어별 RSS 수집
        queries = sec.get("search_terms", [])[:3]
        # 기업명 조합 검색어 추가
        if sec["kr_keywords"] and sec["us_keywords"]:
            kr = sec["kr_keywords"][0]
            us = sec["us_keywords"][0]
            queries.append(f"{kr} {us}")

        for q in queries[:3]:
            items = fetch_google_rss(q, max_items=2)
            for item in items:
                t = item["title"]
                # 중복 제거
                key = t[:30]
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                sentiment = classify_sentiment(t)
                impact    = impact_score(t, sec)

                # 관련 기업 추출
                related_kr = [k for k in sec["kr_keywords"] if k in t]
                related_us = [k for k in sec["us_keywords"] if k.lower() in t.lower()]

                sector_issues.append({
                    "title":      t,
                    "link":       item["link"],
                    "pub":        item["pub"],
                    "source":     item["source"],
                    "sentiment":  sentiment,
                    "impact":     impact,
                    "related_kr": related_kr[:2],
                    "related_us": related_us[:2],
                    "query":      q,
                })
                print(f"    {'✅' if sentiment=='positive' else '⚠️' if sentiment=='negative' else '➡️'} [{sentiment}] {t[:50]}...")

            time.sleep(0.3)  # 요청 간격

        # 임팩트 순 정렬, 최대 8개
        sector_issues.sort(key=lambda x: x["impact"], reverse=True)

        # 섹터에 이슈가 없으면 기본 메시지
        if not sector_issues:
            sector_issues.append({
                "title":     f"{sec['name']} 섹터 최신 이슈를 수집 중입니다.",
                "link":      "",
                "pub":       NOW.strftime('%m/%d %H:%M'),
                "source":    "",
                "sentiment": "neutral",
                "impact":    1,
                "related_kr":[],
                "related_us":[],
                "query":     "",
            })

        colors = COLOR_MAP.get(sec["color"], COLOR_MAP["blue"])

        all_issues.append({
            "id":          sec["id"],
            "name":        sec["name"],
            "icon":        sec["icon"],
            "color":       sec["color"],
            "colors":      colors,
            "kr_stocks":   sec.get("kr_stocks", []),
            "us_stocks":   sec.get("us_stocks", []),
            "kr_keywords": sec["kr_keywords"][:3],
            "us_keywords": sec["us_keywords"][:3],
            "issues":      sector_issues[:8],
            "pos_count":   sum(1 for i in sector_issues if i["sentiment"] == "positive"),
            "neg_count":   sum(1 for i in sector_issues if i["sentiment"] == "negative"),
            "hot":         any(i["impact"] >= 5 for i in sector_issues),
        })

    # 정렬: 핫 섹터 먼저, 그 다음 긍정 이슈 많은 순
    all_issues.sort(key=lambda x: (x["hot"], x["pos_count"] - x["neg_count"]), reverse=True)

    output = {
        "generated_at":     NOW.strftime("%Y년 %m월 %d일 %H:%M (KST)"),
        "generated_at_iso": NOW.isoformat(),
        "total_sectors":    len(all_issues),
        "total_issues":     sum(len(s["issues"]) for s in all_issues),
        "hot_sectors":      [s["name"] for s in all_issues if s["hot"]],
        "sectors":          all_issues,
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/issues.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 62)
    print(f"✅ 완료! docs/issues.json 저장")
    print(f"📊 총 {len(all_issues)}개 섹터 / {output['total_issues']}개 이슈")
    if output["hot_sectors"]:
        print(f"🔥 HOT 섹터: {', '.join(output['hot_sectors'])}")
    print("=" * 62)


if __name__ == "__main__":
    main()
