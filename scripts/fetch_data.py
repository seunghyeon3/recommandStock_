#!/usr/bin/env python3
"""
미국→한국 섹터 분석 데이터 수집 스크립트
매일 미국 장 종료 후 GitHub Actions에서 실행
"""

import json
import os
from datetime import datetime, timedelta
import pytz

try:
    import yfinance as yf
    print("yfinance loaded successfully")
except ImportError:
    print("Installing yfinance...")
    os.system("pip install yfinance")
    import yfinance as yf

# ─── 섹터 정의 ───────────────────────────────────────────────────────────────
SECTORS = [
    {
        "id": "tech",
        "name": "기술·반도체",
        "name_en": "Technology & Semiconductors",
        "icon": "💾",
        "etfs": ["XLK", "SOXX", "SMH"],
        "description": "AI·반도체·클라우드 중심 성장 섹터",
        "korean_stocks": [
            {"ticker": "005930", "name": "삼성전자", "reason": "글로벌 반도체 리더"},
            {"ticker": "000660", "name": "SK하이닉스", "reason": "HBM 메모리 수혜"},
            {"ticker": "042700", "name": "한미반도체", "reason": "HBM 본딩 장비 독점"},
            {"ticker": "267260", "name": "HD현대일렉트릭", "reason": "AI데이터센터 전력"},
            {"ticker": "086520", "name": "에코프로", "reason": "2차전지·소재 연계"},
            {"ticker": "005290", "name": "동진쎄미켐", "reason": "반도체 포토레지스트"},
            {"ticker": "036930", "name": "주성엔지니어링", "reason": "반도체 증착 장비"},
            {"ticker": "196170", "name": "알테오젠", "reason": "바이오·기술 크로스"},
            {"ticker": "012450", "name": "한화에어로스페이스", "reason": "방산·우주 기술"},
            {"ticker": "240810", "name": "원익IPS", "reason": "반도체 장비 국산화"},
        ]
    },
    {
        "id": "ai",
        "name": "AI·소프트웨어",
        "name_en": "AI & Software",
        "icon": "🤖",
        "etfs": ["AIQ", "BOTZ", "ARKK"],
        "description": "생성AI·데이터·플랫폼 고성장 섹터",
        "korean_stocks": [
            {"ticker": "035420", "name": "NAVER", "reason": "하이퍼클로바X AI 선도"},
            {"ticker": "035720", "name": "카카오", "reason": "AI 카카오 전환 기대"},
            {"ticker": "259960", "name": "크래프톤", "reason": "게임AI 융합"},
            {"ticker": "041510", "name": "에스엠", "reason": "AI 엔터테인먼트"},
            {"ticker": "263750", "name": "펄어비스", "reason": "AI 게임 개발사"},
            {"ticker": "030200", "name": "KT", "reason": "AI 인프라·통신"},
            {"ticker": "017670", "name": "SK텔레콤", "reason": "AI 에이전트 사업"},
            {"ticker": "053800", "name": "안랩", "reason": "AI 보안 솔루션"},
            {"ticker": "032800", "name": "판타지오", "reason": "AI 콘텐츠 생성"},
            {"ticker": "047560", "name": "이스트소프트", "reason": "AI 영상 솔루션"},
        ]
    },
    {
        "id": "energy",
        "name": "에너지·원자재",
        "name_en": "Energy & Materials",
        "icon": "⚡",
        "etfs": ["XLE", "XLB", "URA"],
        "description": "원유·원자력·희토류 자원 섹터",
        "korean_stocks": [
            {"ticker": "015760", "name": "한국전력", "reason": "원자력 발전 핵심"},
            {"ticker": "036460", "name": "한국가스공사", "reason": "LNG 에너지 인프라"},
            {"ticker": "267270", "name": "HD현대중공업", "reason": "LNG선 수주 최강"},
            {"ticker": "009540", "name": "HD한국조선해양", "reason": "글로벌 조선 1위"},
            {"ticker": "006360", "name": "GS건설", "reason": "에너지 플랜트 수출"},
            {"ticker": "010120", "name": "LS ELECTRIC", "reason": "전력 인프라 설비"},
            {"ticker": "001230", "name": "동국제강", "reason": "철강·에너지 소재"},
            {"ticker": "047050", "name": "포스코인터내셔널", "reason": "LNG·미네랄 트레이딩"},
            {"ticker": "005490", "name": "POSCO홀딩스", "reason": "2차전지 소재·철강"},
            {"ticker": "011790", "name": "SKC", "reason": "동박·소재 에너지연계"},
        ]
    },
    {
        "id": "finance",
        "name": "금융·은행",
        "name_en": "Financials & Banking",
        "icon": "🏦",
        "etfs": ["XLF", "KRE", "KBE"],
        "description": "금리·신용·자산관리 핵심 섹터",
        "korean_stocks": [
            {"ticker": "105560", "name": "KB금융", "reason": "국내 최대 금융그룹"},
            {"ticker": "055550", "name": "신한지주", "reason": "글로벌 금융 확장"},
            {"ticker": "086790", "name": "하나금융지주", "reason": "외환·투자 강점"},
            {"ticker": "316140", "name": "우리금융지주", "reason": "배당·수익성 개선"},
            {"ticker": "000810", "name": "삼성화재", "reason": "손보 1위 수익성"},
            {"ticker": "032830", "name": "삼성생명", "reason": "생보 시장 1위"},
            {"ticker": "003540", "name": "대신증권", "reason": "증권·투자 수혜"},
            {"ticker": "071050", "name": "한국금융지주", "reason": "한투 계열 증권"},
            {"ticker": "016360", "name": "삼성증권", "reason": "리테일 강자"},
            {"ticker": "001270", "name": "부국증권", "reason": "소형 고배당 증권"},
        ]
    },
    {
        "id": "health",
        "name": "헬스케어·바이오",
        "name_en": "Healthcare & Biotech",
        "icon": "🧬",
        "etfs": ["XLV", "IBB", "XBI"],
        "description": "신약·의료기기·바이오시밀러 성장 섹터",
        "korean_stocks": [
            {"ticker": "068270", "name": "셀트리온", "reason": "바이오시밀러 글로벌"},
            {"ticker": "207940", "name": "삼성바이오로직스", "reason": "CMO 세계 1위"},
            {"ticker": "128940", "name": "한미약품", "reason": "비만치료제 개발"},
            {"ticker": "196170", "name": "알테오젠", "reason": "SC 플랫폼 혁신"},
            {"ticker": "145720", "name": "덴티움", "reason": "치과 임플란트 수출"},
            {"ticker": "086900", "name": "메디톡스", "reason": "보툴리눔 톡신"},
            {"ticker": "285130", "name": "SK바이오팜", "reason": "뇌전증 신약 수출"},
            {"ticker": "377300", "name": "카카오페이", "reason": "헬스케어 금융연계"},
            {"ticker": "214450", "name": "파마리서치", "reason": "재생의료 소재"},
            {"ticker": "009420", "name": "한올바이오파마", "reason": "안과질환 신약"},
        ]
    },
    {
        "id": "consumer",
        "name": "소비재·유통",
        "name_en": "Consumer & Retail",
        "icon": "🛍️",
        "etfs": ["XLY", "XLP", "FDIS"],
        "description": "경기소비재·필수소비재·리테일 섹터",
        "korean_stocks": [
            {"ticker": "005380", "name": "현대차", "reason": "글로벌 전기차 확장"},
            {"ticker": "000270", "name": "기아", "reason": "SUV·전기차 수출"},
            {"ticker": "004170", "name": "신세계", "reason": "프리미엄 유통 강자"},
            {"ticker": "069960", "name": "현대백화점", "reason": "고급 소비 리더"},
            {"ticker": "282330", "name": "BGF리테일", "reason": "편의점 1위 CU"},
            {"ticker": "139480", "name": "이마트", "reason": "대형마트 1위"},
            {"ticker": "271560", "name": "오리온", "reason": "중국·동남아 확장"},
            {"ticker": "097950", "name": "CJ제일제당", "reason": "K-푸드 글로벌화"},
            {"ticker": "036460", "name": "한국가스공사", "reason": "에너지 소비 연계"},
            {"ticker": "161390", "name": "한국타이어앤테크놀로지", "reason": "전기차 타이어 수혜"},
        ]
    },
    {
        "id": "industrial",
        "name": "산업·방산",
        "name_en": "Industrials & Defense",
        "icon": "🏭",
        "etfs": ["XLI", "ITA", "PPA"],
        "description": "제조·방위산업·인프라 핵심 섹터",
        "korean_stocks": [
            {"ticker": "012450", "name": "한화에어로스페이스", "reason": "K방산 수출 선도"},
            {"ticker": "047810", "name": "한국항공우주", "reason": "FA-50 수출 급증"},
            {"ticker": "064350", "name": "현대로템", "reason": "K2전차 수출"},
            {"ticker": "272210", "name": "한화시스템", "reason": "방산전자·SAR위성"},
            {"ticker": "000880", "name": "한화", "reason": "방산 지주 종합"},
            {"ticker": "329180", "name": "현대중공업", "reason": "함정·잠수함 수출"},
            {"ticker": "006800", "name": "미래에셋증권", "reason": "방산 투자 연계"},
            {"ticker": "034020", "name": "두산에너빌리티", "reason": "원전·방산 복합"},
            {"ticker": "267270", "name": "HD현대중공업", "reason": "해양방산 수출"},
            {"ticker": "009830", "name": "한화솔루션", "reason": "방산화학 소재"},
        ]
    },
    {
        "id": "realestate",
        "name": "부동산·인프라",
        "name_en": "Real Estate & Infrastructure",
        "icon": "🏗️",
        "etfs": ["XLRE", "VNQ", "IYR"],
        "description": "리츠·데이터센터·물류인프라 섹터",
        "korean_stocks": [
            {"ticker": "016360", "name": "삼성증권", "reason": "리츠 투자 연계"},
            {"ticker": "006360", "name": "GS건설", "reason": "대형 건설 인프라"},
            {"ticker": "000720", "name": "현대건설", "reason": "해외 플랜트 수주"},
            {"ticker": "047040", "name": "대우건설", "reason": "주택·인프라 복합"},
            {"ticker": "011200", "name": "HMM", "reason": "해운 물류 인프라"},
            {"ticker": "035810", "name": "이지스레지던스리츠", "reason": "주거용 리츠"},
            {"ticker": "088790", "name": "진에어", "reason": "물류·항공 인프라"},
            {"ticker": "003030", "name": "세아제강", "reason": "건설 철강 소재"},
            {"ticker": "000100", "name": "유한양행", "reason": "의료인프라 연계"},
            {"ticker": "010780", "name": "아이에스동서", "reason": "환경·인프라 건설"},
        ]
    },
    {
        "id": "communication",
        "name": "통신·미디어",
        "name_en": "Communication & Media",
        "icon": "📡",
        "etfs": ["XLC", "IYZ", "FCOM"],
        "description": "5G·콘텐츠·플랫폼 미디어 섹터",
        "korean_stocks": [
            {"ticker": "017670", "name": "SK텔레콤", "reason": "5G·AI 통신 선도"},
            {"ticker": "030200", "name": "KT", "reason": "B2B AI·클라우드"},
            {"ticker": "032640", "name": "LG유플러스", "reason": "B2C 5G 서비스"},
            {"ticker": "035420", "name": "NAVER", "reason": "콘텐츠 플랫폼 1위"},
            {"ticker": "035720", "name": "카카오", "reason": "메신저·콘텐츠 생태계"},
            {"ticker": "041510", "name": "에스엠", "reason": "K팝 콘텐츠 글로벌"},
            {"ticker": "352820", "name": "하이브", "reason": "K팝 IP 플랫폼"},
            {"ticker": "035900", "name": "JYP Ent.", "reason": "스트리밍 음원 수혜"},
            {"ticker": "122870", "name": "와이지엔터테인먼트", "reason": "K팝 아이피 확장"},
            {"ticker": "036570", "name": "엔씨소프트", "reason": "게임·메타버스 연계"},
        ]
    },
    {
        "id": "cleanenergy",
        "name": "클린에너지·배터리",
        "name_en": "Clean Energy & Batteries",
        "icon": "🔋",
        "etfs": ["ICLN", "QCLN", "LIT"],
        "description": "태양광·풍력·전기차 배터리 섹터",
        "korean_stocks": [
            {"ticker": "373220", "name": "LG에너지솔루션", "reason": "배터리 글로벌 2위"},
            {"ticker": "006400", "name": "삼성SDI", "reason": "전고체 배터리 선도"},
            {"ticker": "051910", "name": "LG화학", "reason": "배터리 소재 수직계열"},
            {"ticker": "086520", "name": "에코프로", "reason": "양극재 국내 1위"},
            {"ticker": "247540", "name": "에코프로비엠", "reason": "고성능 양극재"},
            {"ticker": "009830", "name": "한화솔루션", "reason": "태양광 모듈 수출"},
            {"ticker": "011790", "name": "SKC", "reason": "동박·배터리 소재"},
            {"ticker": "003670", "name": "포스코퓨처엠", "reason": "음극재·양극재 종합"},
            {"ticker": "402340", "name": "SK스퀘어", "reason": "배터리 투자 지주"},
            {"ticker": "278280", "name": "천보", "reason": "전해질 리튬염 독점"},
        ]
    },
]

# ─── ETF 데이터 수집 ────────────────────────────────────────────────────────
def get_etf_score(tickers):
    """ETF 상승률 기반 섹터 점수 계산"""
    total_score = 0
    count = 0
    details = []
    
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                
                # 1개월 모멘텀
                hist_1m = t.history(period="1mo")
                if len(hist_1m) >= 2:
                    month_change = ((hist_1m['Close'].iloc[-1] - hist_1m['Close'].iloc[0]) / hist_1m['Close'].iloc[0]) * 100
                else:
                    month_change = 0
                
                # 거래량 모멘텀
                vol_ratio = 1.0
                if len(hist) >= 5:
                    avg_vol = hist['Volume'].iloc[:-1].mean()
                    cur_vol = hist['Volume'].iloc[-1]
                    vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1.0
                
                # 점수 = 일간변동 * 0.4 + 월간변동 * 0.4 + 거래량모멘텀 * 0.2
                score = change_pct * 0.4 + month_change * 0.4 + (vol_ratio - 1) * 20 * 0.2
                
                total_score += score
                count += 1
                details.append({
                    "ticker": ticker,
                    "price": round(current, 2),
                    "change_pct": round(change_pct, 2),
                    "month_change": round(month_change, 2),
                    "vol_ratio": round(vol_ratio, 2)
                })
        except Exception as e:
            print(f"  ETF {ticker} 오류: {e}")
    
    avg_score = total_score / count if count > 0 else 0
    return round(avg_score, 2), details

def get_sector_news(sector_name):
    """섹터 관련 뉴스 요약 (기본 메시지)"""
    news_templates = {
        "tech": "반도체 AI 수요 급증으로 글로벌 빅테크 투자 확대 중. HBM 메모리 공급 부족 지속.",
        "ai": "생성AI 채택 가속화로 소프트웨어 기업 실적 상향 조정. 클라우드 지출 증가세.",
        "energy": "원유 공급 불안과 원전 르네상스로 에너지 섹터 주목. LNG 수요 증가 지속.",
        "finance": "금리 고점 확인 후 은행주 밸류에이션 재평가. 대출 성장 회복 기대.",
        "health": "비만치료제·GLP-1 성장 지속. 바이오시밀러 유럽·미국 시장 확대.",
        "consumer": "미국 소비자 지출 견조. K-브랜드 글로벌 프리미엄화 가속.",
        "industrial": "K방산 수출 사상 최대. NATO 국방비 증액에 한국 방산주 수혜.",
        "realestate": "데이터센터 리츠 급성장. AI 인프라 투자로 산업용 부동산 수요 폭발.",
        "communication": "K팝·K드라마 글로벌 스트리밍 성장. 5G 킬러콘텐츠 수익화 본격화.",
        "cleanenergy": "IRA 보조금 효과 지속. 전고체 배터리 상용화 타임라인 가시화.",
    }
    return news_templates.get(sector_name, "글로벌 시장 동향 업데이트 중.")

# ─── 메인 실행 ───────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🔍 미국→한국 섹터 분석 데이터 수집 시작")
    print("=" * 60)
    
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    
    results = []
    
    for i, sector in enumerate(SECTORS):
        print(f"\n[{i+1}/{len(SECTORS)}] {sector['icon']} {sector['name']} 처리 중...")
        print(f"  ETF: {', '.join(sector['etfs'])}")
        
        score, etf_details = get_etf_score(sector['etfs'])
        news = get_sector_news(sector['id'])
        
        # 점수 등급 계산
        if score >= 2:
            grade = "🔥 강력매수"
            grade_color = "hot"
        elif score >= 0.5:
            grade = "📈 매수"
            grade_color = "buy"
        elif score >= -0.5:
            grade = "➡️ 중립"
            grade_color = "neutral"
        elif score >= -2:
            grade = "📉 관망"
            grade_color = "watch"
        else:
            grade = "❄️ 회피"
            grade_color = "cold"
        
        result = {
            "id": sector["id"],
            "name": sector["name"],
            "name_en": sector["name_en"],
            "icon": sector["icon"],
            "description": sector["description"],
            "score": score,
            "grade": grade,
            "grade_color": grade_color,
            "news": news,
            "etf_details": etf_details,
            "korean_stocks": sector["korean_stocks"],
            "updated_at": now_kst.strftime("%Y-%m-%d %H:%M"),
            "updated_at_full": now_kst.isoformat(),
        }
        
        results.append(result)
        print(f"  ✅ 점수: {score:+.2f} | 등급: {grade}")
    
    # 점수 기준 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 순위 부여
    for rank, item in enumerate(results, 1):
        item["rank"] = rank
    
    # 최종 데이터 구조
    output = {
        "generated_at": now_kst.strftime("%Y년 %m월 %d일 %H:%M (KST)"),
        "generated_at_iso": now_kst.isoformat(),
        "total_sectors": len(results),
        "top_sector": results[0]["name"] if results else "",
        "market_date": (now_kst - timedelta(hours=14)).strftime("%Y-%m-%d"),
        "sectors": results,
    }
    
    # docs 폴더가 없으면 생성
    os.makedirs("docs", exist_ok=True)
    
    output_path = "docs/sectors.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ 완료! {output_path} 저장됨")
    print(f"📊 총 {len(results)}개 섹터 분석")
    print(f"🏆 TOP 섹터: {results[0]['name']} (점수: {results[0]['score']:+.2f})")
    print("=" * 60)

if __name__ == "__main__":
    main()
