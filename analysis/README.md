# 분석 파이프라인

Python 3.9+ / `pandas openpyxl pyreadstat==1.2.6 networkx matplotlib`

## 데이터 소스
1. **국민여행조사 2025 국내여행 원자료** (`.SAV`) — 관광지식정보시스템(know.tour.go.kr) 다운로드. *원자료는 라이선스상 저장소에 미포함.*
2. **지역별 방문자수 API** — data.go.kr 15101972, 활용신청 후 서비스키 발급.
3. **국가유산 검색 API** — cha.go.kr, 무인증키.

## 단계

### ① 동선 네트워크 (국민여행조사)
- `D_TRA{k}_{v}_SPOT` = 여행차수 k의 v번째 방문지(시군구 5자리코드). 순서대로 읽어 시퀀스 구성.
- 연속쌍 (A→B, A≠B)을 방향엣지로, WT_DOM 가중 합산.
- `networkx.DiGraph` → `degree_centrality`, `betweenness_centrality`.

### ② 매력쇠퇴 (국민여행조사)
- `A10`(재방문의향)·`A11`(추천의향) 1~5척도. A섹션=대표여행(≈여행1차)이므로 **여행1차 방문지역에 귀속**.
- 지역별 가중평균 → z(−재방문), z(−추천).

### ③ 방문쇠퇴 (방문자수 API) — `pull_locgo.py`
```
GET https://apis.data.go.kr/B551011/DataLabService/locgoRegnVisitrDDList
  ?serviceKey=<KEY>&numOfRows=9000&pageNo=&MobileOS=ETC&MobileApp=t
  &startYmd=YYYY0101&endYmd=YYYY1231&_type=json
```
- 반환: `signguCode`(행정표준코드 5자리)·`signguNm`·`touDivCd`(1현지인/2외지인/3외국인)·`touNum`·`baseYmd`.
- **외지인(touDivCd=2)** 연간 합산(2019·2022·2024) → 회복률(24/19)·최근추세(24/22).
- ⚠️ 월별 없음(일별만). 시도 엔드포인트는 `metcoRegnVisitrDDList`.

### 문화유산 밀도·좌표 (국가유산 API)
```
GET https://www.cha.go.kr/cha/SearchKindOpenapiList.do
  ?ccbaCtcd=<시도코드>&pageUnit=990&pageIndex=&ccbaCncl=N
```
- XML. `ccbaCtcdNm`·`ccsiName`(시군구)·`ccmaName`(종목)·`longitude`/`latitude`.
- ⚠️ `ccbaCtcd=24`는 "전남광주"(광주+전남 통합), 세종=45. `ccbaCncl=N`(현존 지정)만 집계, 고유번호로 중복제거 → 전국 15,728건.

### 복합지수 통합 (v3)
- 세 축 z-표준화 등가중 평균. 표본 30건↑ 시군구, **대도시 자치구 제외**(도지역 시군 145개).
- API(행정표준코드) ↔ 설문(설문코드)는 **시도명+시군구명으로 매칭**(190/191). 정규화 필요: 강원특별자치도/강원도, 전북특별자치도/전라북도 등.
- 문화유산 밀도와 교차 → "쇠퇴 × 문화유산 잠재력" 매트릭스.

## 코드체계 주의
| 시도 | 국민여행조사 | 방문자수 API(행정표준) | 국가유산(ccbaCtcd) |
|---|---|---|---|
| 부산 | 21 | 26 | 21 |
| 대구 | 22 | 27 | 22 |
| 세종 | 29 | 36 | 45 |
| 제주 | 39 | 50 | 50 |
→ **코드 직접 매칭 금지, 이름으로 매칭.**

## 산출물
- `data/changnyeong_heritage.json` — 창녕 국가유산(좌표) 루트 후보
- `data/heritage_density.pkl` — 시군구별 문화유산 수
- 지도용 최종: `../map/data/targets.json`(활성화 타깃16), `../map/data/routes.json`(창녕 루트)
