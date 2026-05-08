#!/usr/bin/env python3
"""
미국→한국 섹터 분석 - 복합 점수 모델 v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
점수 구성 (100점 만점):
  ETF 등락률    30% ← 미국 섹터 방향성
  SOX/필라델피아 15% ← 반도체 민감도
  DXY 달러지수  15% ← 환율 매크로
  미국채 10년물  15% ← 금리 민감도
  중국 CSI300  15% ← 중국 수요 (수출)
  VIX 공포지수  10% ← 리스크 온/오프
"""

import json, os, sys
from datetime import datetime, timedelta
import pytz

try:
    import yfinance as yf
except ImportError:
    os.system("pip install yfinance --break-system-packages -q")
    import yfinance as yf

# ─── 섹터 정의 ────────────────────────────────────────────────
SECTORS = [
    {
        "id": "tech",
        "name": "기술·반도체",
        "name_en": "Technology & Semiconductors",
        "icon": "💾",
        "etfs": ["XLK", "SOXX", "SMH"],
        # 섹터별 매크로 민감도 가중치 (합=1.0)
        # dxy↑→수출유리, rate↑→성장주불리, china↑→소재/수출유리, vix↑→리스크오프
        "sensitivity": {
            "etf": 0.30, "sox": 0.25, "dxy": 0.10,
            "rate": -0.15, "china": 0.10, "vix": -0.10
        },
        "description": "AI·반도체·클라우드 중심 성장 섹터",
        "korean_stocks": [
            {"ticker": "005930", "name": "삼성전자",         "reason": "글로벌 반도체 리더"},
            {"ticker": "000660", "name": "SK하이닉스",        "reason": "HBM 메모리 핵심 수혜"},
            {"ticker": "042700", "name": "한미반도체",         "reason": "HBM 본딩 장비 독점"},
            {"ticker": "267260", "name": "HD현대일렉트릭",     "reason": "AI 데이터센터 전력"},
            {"ticker": "005290", "name": "동진쎄미켐",         "reason": "반도체 포토레지스트"},
            {"ticker": "036930", "name": "주성엔지니어링",      "reason": "반도체 증착 장비"},
            {"ticker": "240810", "name": "원익IPS",           "reason": "반도체 장비 국산화"},
            {"ticker": "046890", "name": "서울반도체",          "reason": "LED·반도체 패키지"},
            {"ticker": "012450", "name": "한화에어로스페이스",   "reason": "우주·반도체 융합"},
            {"ticker": "336370", "name": "솔루스첨단소재",      "reason": "동박·반도체 소재"},
        ]
    },
    {
        "id": "ai",
        "name": "AI·소프트웨어",
        "name_en": "AI & Software",
        "icon": "🤖",
        "etfs": ["AIQ", "BOTZ", "ARKK"],
        "sensitivity": {
            "etf": 0.35, "sox": 0.15, "dxy": 0.05,
            "rate": -0.25, "china": 0.05, "vix": -0.15
        },
        "description": "생성AI·데이터·플랫폼 고성장 섹터",
        "korean_stocks": [
            {"ticker": "035420", "name": "NAVER",            "reason": "하이퍼클로바X AI 선도"},
            {"ticker": "035720", "name": "카카오",            "reason": "AI 전환 기대"},
            {"ticker": "259960", "name": "크래프톤",           "reason": "게임 AI 융합"},
            {"ticker": "030200", "name": "KT",               "reason": "AI 인프라·클라우드"},
            {"ticker": "017670", "name": "SK텔레콤",          "reason": "AI 에이전트 사업"},
            {"ticker": "053800", "name": "안랩",              "reason": "AI 보안 솔루션"},
            {"ticker": "047560", "name": "이스트소프트",        "reason": "AI 영상 솔루션"},
            {"ticker": "263750", "name": "펄어비스",           "reason": "AI 게임 개발"},
            {"ticker": "041510", "name": "에스엠",            "reason": "AI 엔터 플랫폼"},
            {"ticker": "036570", "name": "엔씨소프트",         "reason": "AI NPC·메타버스"},
        ]
    },
    {
        "id": "energy",
        "name": "에너지·원자재",
        "name_en": "Energy & Materials",
        "icon": "⚡",
        "etfs": ["XLE", "XLB", "URA"],
        "sensitivity": {
            "etf": 0.25, "sox": -0.05, "dxy": -0.20,
            "rate": 0.05, "china": 0.30, "vix": -0.15
        },
        "description": "원유·원자력·희토류 자원 섹터",
        "korean_stocks": [
            {"ticker": "015760", "name": "한국전력",          "reason": "원자력 발전 핵심"},
            {"ticker": "036460", "name": "한국가스공사",        "reason": "LNG 에너지 인프라"},
            {"ticker": "009540", "name": "HD한국조선해양",      "reason": "LNG선 수주 1위"},
            {"ticker": "267270", "name": "HD현대중공업",        "reason": "LNG·해양플랜트"},
            {"ticker": "010120", "name": "LS ELECTRIC",       "reason": "전력 인프라 설비"},
            {"ticker": "047050", "name": "포스코인터내셔널",     "reason": "LNG·미네랄 트레이딩"},
            {"ticker": "005490", "name": "POSCO홀딩스",        "reason": "철강·2차전지 소재"},
            {"ticker": "006360", "name": "GS건설",            "reason": "에너지 플랜트 수출"},
            {"ticker": "034020", "name": "두산에너빌리티",       "reason": "원전 핵심 기자재"},
            {"ticker": "011790", "name": "SKC",              "reason": "동박·에너지 소재"},
        ]
    },
    {
        "id": "finance",
        "name": "금융·은행",
        "name_en": "Financials & Banking",
        "icon": "🏦",
        "etfs": ["XLF", "KRE", "KBE"],
        "sensitivity": {
            "etf": 0.30, "sox": -0.05, "dxy": 0.10,
            "rate": 0.30, "china": 0.05, "vix": -0.20
        },
        "description": "금리·신용·자산관리 핵심 섹터",
        "korean_stocks": [
            {"ticker": "105560", "name": "KB금융",            "reason": "국내 최대 금융그룹"},
            {"ticker": "055550", "name": "신한지주",           "reason": "글로벌 금융 확장"},
            {"ticker": "086790", "name": "하나금융지주",        "reason": "외환·투자 강점"},
            {"ticker": "316140", "name": "우리금융지주",        "reason": "배당·수익성 개선"},
            {"ticker": "000810", "name": "삼성화재",           "reason": "손보 1위 수익성"},
            {"ticker": "032830", "name": "삼성생명",           "reason": "생보 시장 1위"},
            {"ticker": "071050", "name": "한국금융지주",        "reason": "한투 계열 증권"},
            {"ticker": "016360", "name": "삼성증권",           "reason": "리테일 강자"},
            {"ticker": "003540", "name": "대신증권",           "reason": "증권·투자 수혜"},
            {"ticker": "001270", "name": "부국증권",           "reason": "소형 고배당 증권"},
        ]
    },
    {
        "id": "health",
        "name": "헬스케어·바이오",
        "name_en": "Healthcare & Biotech",
        "icon": "🧬",
        "etfs": ["XLV", "IBB", "XBI"],
        "sensitivity": {
            "etf": 0.35, "sox": 0.00, "dxy": -0.05,
            "rate": -0.30, "china": 0.10, "vix": -0.20
        },
        "description": "신약·의료기기·바이오시밀러 성장 섹터",
        "korean_stocks": [
            {"ticker": "068270", "name": "셀트리온",           "reason": "바이오시밀러 글로벌"},
            {"ticker": "207940", "name": "삼성바이오로직스",     "reason": "CMO 세계 1위"},
            {"ticker": "128940", "name": "한미약품",           "reason": "비만치료제 개발"},
            {"ticker": "196170", "name": "알테오젠",           "reason": "SC 플랫폼 혁신"},
            {"ticker": "145720", "name": "덴티움",            "reason": "치과 임플란트 수출"},
            {"ticker": "086900", "name": "메디톡스",           "reason": "보툴리눔 톡신"},
            {"ticker": "285130", "name": "SK바이오팜",         "reason": "뇌전증 신약 수출"},
            {"ticker": "214450", "name": "파마리서치",          "reason": "재생의료 소재"},
            {"ticker": "009420", "name": "한올바이오파마",       "reason": "안과질환 신약"},
            {"ticker": "000100", "name": "유한양행",           "reason": "신약 라이선스아웃"},
        ]
    },
    {
        "id": "consumer",
        "name": "소비재·유통",
        "name_en": "Consumer & Retail",
        "icon": "🛍️",
        "etfs": ["XLY", "XLP", "FDIS"],
        "sensitivity": {
            "etf": 0.30, "sox": 0.00, "dxy": -0.15,
            "rate": -0.10, "china": 0.25, "vix": -0.20
        },
        "description": "경기소비재·필수소비재·리테일 섹터",
        "korean_stocks": [
            {"ticker": "005380", "name": "현대차",            "reason": "글로벌 전기차 확장"},
            {"ticker": "000270", "name": "기아",              "reason": "SUV·전기차 수출"},
            {"ticker": "004170", "name": "신세계",            "reason": "프리미엄 유통 강자"},
            {"ticker": "069960", "name": "현대백화점",          "reason": "고급 소비 리더"},
            {"ticker": "282330", "name": "BGF리테일",          "reason": "편의점 1위 CU"},
            {"ticker": "139480", "name": "이마트",            "reason": "대형마트 1위"},
            {"ticker": "271560", "name": "오리온",            "reason": "중국·동남아 확장"},
            {"ticker": "097950", "name": "CJ제일제당",         "reason": "K-푸드 글로벌화"},
            {"ticker": "161390", "name": "한국타이어앤테크놀로지", "reason": "전기차 타이어 수혜"},
            {"ticker": "004990", "name": "롯데지주",           "reason": "유통 복합 포트폴리오"},
        ]
    },
    {
        "id": "industrial",
        "name": "산업·방산",
        "name_en": "Industrials & Defense",
        "icon": "🏭",
        "etfs": ["XLI", "ITA", "PPA"],
        "sensitivity": {
            "etf": 0.30, "sox": 0.05, "dxy": 0.15,
            "rate": 0.05, "china": 0.15, "vix": 0.30
        },
        "description": "제조·방위산업·인프라 핵심 섹터",
        "korean_stocks": [
            {"ticker": "012450", "name": "한화에어로스페이스",   "reason": "K방산 수출 선도"},
            {"ticker": "047810", "name": "한국항공우주",        "reason": "FA-50 수출 급증"},
            {"ticker": "064350", "name": "현대로템",           "reason": "K2전차·수소열차"},
            {"ticker": "272210", "name": "한화시스템",          "reason": "방산전자·SAR위성"},
            {"ticker": "000880", "name": "한화",              "reason": "방산 지주 종합"},
            {"ticker": "329180", "name": "현대중공업",          "reason": "함정·잠수함 수출"},
            {"ticker": "034020", "name": "두산에너빌리티",       "reason": "원전·방산 복합"},
            {"ticker": "267270", "name": "HD현대중공업",        "reason": "해양방산 수출"},
            {"ticker": "009830", "name": "한화솔루션",          "reason": "방산화학 소재"},
            {"ticker": "047050", "name": "포스코인터내셔널",     "reason": "방산 소재 조달"},
        ]
    },
    {
        "id": "realestate",
        "name": "부동산·인프라",
        "name_en": "Real Estate & Infrastructure",
        "icon": "🏗️",
        "etfs": ["XLRE", "VNQ", "IYR"],
        "sensitivity": {
            "etf": 0.35, "sox": -0.05, "dxy": -0.10,
            "rate": -0.35, "china": 0.10, "vix": -0.15
        },
        "description": "리츠·데이터센터·물류인프라 섹터",
        "korean_stocks": [
            {"ticker": "006360", "name": "GS건설",            "reason": "대형 건설 인프라"},
            {"ticker": "000720", "name": "현대건설",           "reason": "해외 플랜트 수주"},
            {"ticker": "047040", "name": "대우건설",           "reason": "주택·인프라 복합"},
            {"ticker": "011200", "name": "HMM",              "reason": "해운 물류 인프라"},
            {"ticker": "003030", "name": "세아제강",           "reason": "건설 철강 소재"},
            {"ticker": "010780", "name": "아이에스동서",        "reason": "환경·인프라 건설"},
            {"ticker": "028260", "name": "삼성물산",           "reason": "건설·유통 복합"},
            {"ticker": "000210", "name": "대림산업(DL)",       "reason": "석유화학·건설"},
            {"ticker": "096770", "name": "SK이노베이션",        "reason": "에너지·인프라"},
            {"ticker": "001440", "name": "대한해운",           "reason": "벌크·탱커 해운"},
        ]
    },
    {
        "id": "communication",
        "name": "통신·미디어",
        "name_en": "Communication & Media",
        "icon": "📡",
        "etfs": ["XLC", "IYZ", "FCOM"],
        "sensitivity": {
            "etf": 0.35, "sox": 0.05, "dxy": -0.10,
            "rate": -0.20, "china": 0.15, "vix": -0.15
        },
        "description": "5G·콘텐츠·플랫폼 미디어 섹터",
        "korean_stocks": [
            {"ticker": "017670", "name": "SK텔레콤",          "reason": "5G·AI 통신 선도"},
            {"ticker": "030200", "name": "KT",               "reason": "B2B AI·클라우드"},
            {"ticker": "032640", "name": "LG유플러스",         "reason": "B2C 5G 서비스"},
            {"ticker": "035420", "name": "NAVER",            "reason": "콘텐츠 플랫폼 1위"},
            {"ticker": "035720", "name": "카카오",            "reason": "메신저·콘텐츠 생태계"},
            {"ticker": "041510", "name": "에스엠",            "reason": "K팝 콘텐츠 글로벌"},
            {"ticker": "352820", "name": "하이브",            "reason": "K팝 IP 플랫폼"},
            {"ticker": "035900", "name": "JYP Ent.",         "reason": "스트리밍 음원 수혜"},
            {"ticker": "122870", "name": "와이지엔터테인먼트",   "reason": "K팝 IP 확장"},
            {"ticker": "259960", "name": "크래프톤",           "reason": "게임·미디어 융합"},
        ]
    },
    {
        "id": "cleanenergy",
        "name": "클린에너지·배터리",
        "name_en": "Clean Energy & Batteries",
        "icon": "🔋",
        "etfs": ["ICLN", "QCLN", "LIT"],
        "sensitivity": {
            "etf": 0.30, "sox": 0.05, "dxy": -0.20,
            "rate": -0.20, "china": 0.25, "vix": -0.10
        },
        "description": "태양광·풍력·전기차 배터리 섹터",
        "korean_stocks": [
            {"ticker": "373220", "name": "LG에너지솔루션",      "reason": "배터리 글로벌 2위"},
            {"ticker": "006400", "name": "삼성SDI",           "reason": "전고체 배터리 선도"},
            {"ticker": "051910", "name": "LG화학",            "reason": "배터리 소재 수직계열"},
            {"ticker": "086520", "name": "에코프로",           "reason": "양극재 국내 1위"},
            {"ticker": "247540", "name": "에코프로비엠",        "reason": "고성능 양극재"},
            {"ticker": "009830", "name": "한화솔루션",          "reason": "태양광 모듈 수출"},
            {"ticker": "011790", "name": "SKC",              "reason": "동박·배터리 소재"},
            {"ticker": "003670", "name": "포스코퓨처엠",        "reason": "음극재·양극재 종합"},
            {"ticker": "278280", "name": "천보",              "reason": "전해질 리튬염 독점"},
            {"ticker": "402340", "name": "SK스퀘어",           "reason": "배터리 투자 지주"},
        ]
    },
]

# ─── 매크로 지표 티커 ─────────────────────────────────────────
MACRO_TICKERS = {
    "sox":   "^SOX",    # 필라델피아 반도체지수
    "dxy":   "DX-Y.NYB",# 달러 인덱스
    "rate":  "^TNX",    # 미국 10년물 국채금리
    "china": "000300.SS",# CSI 300 (중국)
    "vix":   "^VIX",    # 공포지수
}

def safe_fetch(ticker, period="5d"):
    """안전하게 yfinance 데이터 수집"""
    try:
        t = yf.Ticker(ticker)
        h = t.history(period=period)
        if len(h) >= 2:
            return h
        return None
    except Exception as e:
        print(f"  ⚠ {ticker} 수집 실패: {e}")
        return None

def pct_change(hist):
    """직전 대비 등락률 (%)"""
    if hist is None or len(hist) < 2:
        return 0.0
    c = hist['Close'].iloc[-1]
    p = hist['Close'].iloc[-2]
    return ((c - p) / p * 100) if p != 0 else 0.0

def month_change(hist):
    """1개월 변동률 (%)"""
    if hist is None or len(hist) < 5:
        return 0.0
    c = hist['Close'].iloc[-1]
    p = hist['Close'].iloc[0]
    return ((c - p) / p * 100) if p != 0 else 0.0

def vol_momentum(hist):
    """거래량 모멘텀 (당일/평균 - 1)"""
    if hist is None or len(hist) < 3:
        return 0.0
    avg = hist['Volume'].iloc[:-1].mean()
    cur = hist['Volume'].iloc[-1]
    return (cur / avg - 1.0) if avg > 0 else 0.0

# ─── 매크로 지표 수집 ─────────────────────────────────────────
def collect_macro():
    """
    매크로 지표별 '방향성 신호' 계산
    ・모든 값은 표준화된 [-3, +3] 범위 점수로 변환
    ・각 섹터의 sensitivity와 곱해서 최종 점수에 반영
    """
    print("\n📡 매크로 지표 수집 중...")
    macro = {}
    raw   = {}

    for key, ticker in MACRO_TICKERS.items():
        h5  = safe_fetch(ticker, "5d")
        h1m = safe_fetch(ticker, "1mo")
        d   = pct_change(h5)
        m   = month_change(h1m)

        # 지표별 방향성 부호 처리
        if key == "dxy":
            # DXY↑ → 수출주 불리(원화약세 이중효과), 원자재↓
            # 섹터별 sensitivity에서 부호로 처리하므로 raw 값 그대로
            signal = d * 0.5 + m * 0.3
        elif key == "rate":
            # 금리↑ → 성장주 불리 (sensitivity에서 음수로 처리)
            signal = d * 0.5 + m * 0.3
        elif key == "vix":
            # VIX↑ → 위험자산 불리 (sensitivity에서 음수로 처리)
            signal = d * 0.4 + m * 0.2
        elif key == "china":
            # CSI300↑ → 한국 수출 수혜
            signal = d * 0.5 + m * 0.3
        elif key == "sox":
            signal = d * 0.5 + m * 0.3
        else:
            signal = d * 0.5 + m * 0.3

        macro[key] = round(signal, 4)
        raw[key]   = {"ticker": ticker, "day_chg": round(d, 3), "month_chg": round(m, 3), "signal": round(signal, 4)}
        status = f"{d:+.2f}% (일) / {m:+.2f}% (월) → signal {signal:+.3f}"
        print(f"  {key.upper():8s} [{ticker}] {status}")

    return macro, raw

# ─── ETF 점수 ─────────────────────────────────────────────────
def collect_etf(etfs):
    details = []
    total   = 0.0
    count   = 0

    for ticker in etfs:
        h5  = safe_fetch(ticker, "5d")
        h1m = safe_fetch(ticker, "1mo")
        if h5 is None:
            continue
        d = pct_change(h5)
        m = month_change(h1m)
        v = vol_momentum(h5)

        price = round(h5['Close'].iloc[-1], 2) if h5 is not None else 0
        # ETF 자체 점수: 일간 40% + 월간 40% + 거래량 20%
        score = d * 0.4 + m * 0.4 + v * 20 * 0.2
        total += score
        count += 1
        details.append({
            "ticker":     ticker,
            "price":      price,
            "change_pct": round(d, 2),
            "month_change": round(m, 2),
            "vol_ratio":  round(v + 1, 2),
            "score":      round(score, 3),
        })

    avg_score = total / count if count > 0 else 0.0
    return round(avg_score, 3), details

# ─── 복합 점수 계산 ───────────────────────────────────────────
def compute_composite(etf_score, macro, sensitivity):
    """
    복합 점수 = ETF점수 × w_etf
              + SOX신호 × w_sox
              + DXY신호 × w_dxy (섹터 민감도 부호 포함)
              + Rate신호 × w_rate
              + China신호 × w_china
              + VIX신호 × w_vix
    """
    s = sensitivity
    score = (
        etf_score            * s.get("etf",   0.30) +
        macro.get("sox", 0)  * s.get("sox",   0.15) +
        macro.get("dxy", 0)  * s.get("dxy",   0.10) +
        macro.get("rate", 0) * s.get("rate",  0.10) +
        macro.get("china",0) * s.get("china", 0.15) +
        macro.get("vix", 0)  * s.get("vix",  -0.10)
    )
    return round(score, 3)

def grade(score):
    if score >= 2.0:
        return "🔥 강력매수", "hot"
    elif score >= 0.5:
        return "📈 매수",     "buy"
    elif score >= -0.5:
        return "➡️ 중립",    "neut"
    elif score >= -2.0:
        return "📉 관망",     "watch"
    else:
        return "❄️ 회피",    "cold"

NEWS_MAP = {
    "tech":        "반도체 AI 수요 급증으로 빅테크 설비투자 확대 중. HBM 메모리 공급 부족 지속.",
    "ai":          "생성AI 채택 가속화로 소프트웨어 기업 실적 상향. 클라우드 지출 증가세.",
    "energy":      "원유 공급 불안과 원전 르네상스로 에너지 섹터 주목. LNG 수요 증가 지속.",
    "finance":     "금리 고점 확인 후 은행주 밸류에이션 재평가. 대출 성장 회복 기대.",
    "health":      "비만치료제·GLP-1 성장 지속. 바이오시밀러 유럽·미국 시장 확대.",
    "consumer":    "미국 소비자 지출 견조. K-브랜드 글로벌 프리미엄화 가속.",
    "industrial":  "K방산 수출 사상 최대. NATO 국방비 증액에 한국 방산주 수혜.",
    "realestate":  "데이터센터 리츠 급성장. AI 인프라 투자로 산업용 부동산 수요 폭발.",
    "communication":"K팝·K드라마 글로벌 스트리밍 성장. 5G 킬러콘텐츠 수익화 본격화.",
    "cleanenergy": "IRA 보조금 효과 지속. 전고체 배터리 상용화 타임라인 가시화.",
}

# ─── 메인 ────────────────────────────────────────────────────
def main():
    print("=" * 62)
    print("🔍 US→KR 섹터 복합 점수 분석 v2 시작")
    print("=" * 62)

    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)

    # 1) 매크로 수집
    macro, macro_raw = collect_macro()

    # 2) 섹터별 처리
    results = []
    print(f"\n📊 섹터 분석 ({len(SECTORS)}개)...")

    for i, sec in enumerate(SECTORS):
        print(f"\n  [{i+1:02d}] {sec['icon']} {sec['name']}")

        etf_score, etf_details = collect_etf(sec["etfs"])
        composite = compute_composite(etf_score, macro, sec["sensitivity"])
        g_label, g_color = grade(composite)

        # 점수 기여도 분해
        s = sec["sensitivity"]
        breakdown = {
            "etf":   round(etf_score            * s.get("etf",  0.30), 3),
            "sox":   round(macro.get("sox",0)   * s.get("sox",  0.15), 3),
            "dxy":   round(macro.get("dxy",0)   * s.get("dxy",  0.10), 3),
            "rate":  round(macro.get("rate",0)  * s.get("rate", 0.10), 3),
            "china": round(macro.get("china",0) * s.get("china",0.15), 3),
            "vix":   round(macro.get("vix",0)   * s.get("vix", -0.10), 3),
        }

        print(f"     ETF={etf_score:+.2f} | 복합={composite:+.2f} | {g_label}")

        results.append({
            "id":           sec["id"],
            "name":         sec["name"],
            "name_en":      sec["name_en"],
            "icon":         sec["icon"],
            "description":  sec["description"],
            "score":        composite,
            "etf_score":    etf_score,
            "grade":        g_label,
            "grade_color":  g_color,
            "news":         NEWS_MAP.get(sec["id"], ""),
            "etfs":         sec["etfs"],
            "etf_details":  etf_details,
            "breakdown":    breakdown,
            "sensitivity":  s,
            "korean_stocks": sec["korean_stocks"],
            "updated_at":   now.strftime("%Y-%m-%d %H:%M"),
        })

    # 3) 정렬 + 순위
    results.sort(key=lambda x: x["score"], reverse=True)
    for rank, r in enumerate(results, 1):
        r["rank"] = rank

    # 4) 출력
    output = {
        "generated_at":     now.strftime("%Y년 %m월 %d일 %H:%M (KST)"),
        "generated_at_iso": now.isoformat(),
        "total_sectors":    len(results),
        "top_sector":       results[0]["name"],
        "market_date":      (now - timedelta(hours=14)).strftime("%Y-%m-%d"),
        "macro_raw":        macro_raw,
        "macro":            macro,
        "sectors":          results,
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/sectors.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 62)
    print(f"✅ 완료! docs/sectors.json 저장")
    print(f"🏆 TOP: {results[0]['name']} ({results[0]['score']:+.2f})")
    print(f"📉 BOTTOM: {results[-1]['name']} ({results[-1]['score']:+.2f})")
    print("=" * 62)

if __name__ == "__main__":
    main()
