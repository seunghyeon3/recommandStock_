# 🌐 미국→한국 섹터 분석 대시보드

**US ETF 기반 섹터 점수로 한국 주도주를 자동 매핑하는 GitHub Pages 대시보드**

[![데이터 자동 업데이트](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/update-data.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/update-data.yml)

---

## 📌 주요 기능

- 🇺🇸 **미국 ETF 10개 섹터** 실시간 점수 계산
- 🇰🇷 **한국 주도주 자동 매핑** (섹터별 10종목)
- 📊 **섹터 점수 자동 정렬** (강력매수 → 회피)
- 🔄 **매일 미국 장 마감 후 자동 업데이트** (GitHub Actions)
- 🌙 **다크모드 / 라이트모드** 지원
- 📱 **모바일 반응형** 지원
- 🎴 **카드 클릭 시 접기/펼치기**

---

## 🚀 GitHub Pages 배포 방법

### 1단계: 레포지토리 생성 및 파일 업로드

```bash
# 이 ZIP 파일을 풀고 GitHub 레포지토리에 업로드
git init
git add .
git commit -m "🚀 초기 배포"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2단계: GitHub Pages 활성화

1. GitHub 레포지토리 → **Settings** 탭 클릭
2. 왼쪽 메뉴 → **Pages** 클릭
3. **Source**: `Deploy from a branch` 선택
4. **Branch**: `main` / `docs` 폴더 선택
5. **Save** 클릭

> 수 분 후 `https://YOUR_USERNAME.github.io/YOUR_REPO/` 에서 확인 가능

### 3단계: GitHub Actions 권한 설정

1. **Settings → Actions → General**
2. **Workflow permissions** → `Read and write permissions` 선택
3. **Save** 클릭

---

## 📁 파일 구조

```
├── .github/
│   └── workflows/
│       └── update-data.yml    # 자동 업데이트 스케줄러
├── scripts/
│   └── fetch_data.py          # yfinance 데이터 수집 스크립트
├── docs/
│   ├── index.html             # 메인 대시보드 (GitHub Pages 서빙)
│   └── sectors.json           # 자동 생성되는 섹터 데이터
└── README.md
```

---

## ⏰ 업데이트 스케줄

| 구분 | 시간 |
|------|------|
| 미국 장 마감 | 오전 5:00 (KST) |
| 데이터 수집 | 오전 6:30 (KST) |
| GitHub Pages 반영 | 오전 6:35~40 (KST) |

---

## 📊 섹터 구성

| # | 섹터 | 추적 ETF |
|---|------|---------|
| 1 | 기술·반도체 | XLK, SOXX, SMH |
| 2 | AI·소프트웨어 | AIQ, BOTZ, ARKK |
| 3 | 에너지·원자재 | XLE, XLB, URA |
| 4 | 금융·은행 | XLF, KRE, KBE |
| 5 | 헬스케어·바이오 | XLV, IBB, XBI |
| 6 | 소비재·유통 | XLY, XLP, FDIS |
| 7 | 산업·방산 | XLI, ITA, PPA |
| 8 | 부동산·인프라 | XLRE, VNQ, IYR |
| 9 | 통신·미디어 | XLC, IYZ, FCOM |
| 10 | 클린에너지·배터리 | ICLN, QCLN, LIT |

---

## 🧮 점수 산출 공식

```
섹터 점수 = ETF 일간변동(%) × 0.4
          + ETF 월간변동(%) × 0.4
          + 거래량 모멘텀     × 0.2
```

| 점수 | 등급 |
|------|------|
| +2.0 이상 | 🔥 강력매수 |
| +0.5 ~ +2.0 | 📈 매수 |
| -0.5 ~ +0.5 | ➡️ 중립 |
| -2.0 ~ -0.5 | 📉 관망 |
| -2.0 미만 | ❄️ 회피 |

---

## ⚠️ 면책 조항

본 프로젝트는 **투자 참고용 정보 제공** 목적으로 제작되었습니다.  
투자 판단의 최종 책임은 투자자 본인에게 있으며, 투자 권유가 아닙니다.
