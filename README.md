# 머무리 (momuri) — 쇠퇴 소도시 관광 활성화 플래너

> **2026 관광데이터 활용 공모전 ②-2 웹·앱 구현 부문 / 지정과제 4번** 출품작
> 해결과제: *"단순 흥미 위주 일회성 관광의 한계 및 인구 감소 지역의 지속가능한 생활인구 유입 대책 부족"*

데이터가 진단한 **"살릴 자원은 있는데 소외된" 쇠퇴 소도시(숨은 매력지)**를 테마로 매칭하고,
한국관광공사 TourAPI 콘텐츠로 코스를 만들어 **체류·재방문(관계인구)**까지 잇는 관광 활성화 서비스.

- 서비스 개념·전략 전체: [`docs/웹앱_기획_과제4.md`](docs/웹앱_기획_과제4.md)
- 지수 방법론: [`map/methodology.html`](map/methodology.html) (또는 아래 재현 절차)
- 분석 엔진은 포스터 프로젝트 `tourgo-tourism-decline`에서 재활용.

---

## 1. 빠른 실행 — 웹 데모 (Python만 있으면 됨, API 키·재계산 불필요)

필요한 데이터(지수·콘텐츠·경계)는 모두 저장소에 포함되어 있어 **클론 후 바로 실행**된다.

```bash
git clone https://github.com/uurimii16/momuri.git
cd momuri/map
python -m http.server 8901
```
브라우저에서:
- 숨은 매력지: http://127.0.0.1:8901/momuri.html
- 시군구 쇠퇴지수 단계구분도: http://127.0.0.1:8901/decline-map.html
- 지표 방법론 설명서: http://127.0.0.1:8901/methodology.html

> Windows는 `map/start.bat` 더블클릭으로도 실행 가능.
> 인터넷 필요(지도 타일 = Routo, 데모 키 내장. 재배포 시 본인 키로 교체 권장).

---

## 2. 폴더 구조

```
momuri/
├─ README.md                     (이 파일)
├─ requirements.txt              (분석 재현용 파이썬 패키지)
├─ docs/웹앱_기획_과제4.md        (서비스 기획·전략 정본)
├─ map/                          (웹 프론트)
│   ├─ momuri.html               숨은 매력지 서비스
│   ├─ decline-map.html          쇠퇴지수 단계구분도(Jenks)
│   ├─ methodology.html          지표 방법론 설명서
│   ├─ index.html / app.js       (구 tourgo 지도 — 참고용, 미사용)
│   └─ data/                     momuri.json · decline_choropleth.geojson · decline_breaks.json ...
└─ analysis/                     (데이터 파이프라인)
    ├─ pull_visits.py            ① 방문자수 API 수집       → data/visits.json
    ├─ build_index.py            ②매력·③연결 (국민여행조사) → data/index_axes.json
    ├─ combine_index.py          3축 통합 복합쇠퇴지수      → data/index_full.json
    ├─ build_candidates.py       숨은매력지 후보(대도시필터) → data/candidates.json
    ├─ build_choropleth.py       시군구 경계+지수(Jenks)    → map/data/decline_choropleth.geojson
    ├─ tourapi_fetch.py          TourAPI 연동 모듈
    └─ build_service_data.py     후보+TourAPI 콘텐츠        → map/data/momuri.json
```

---

## 3. 분석 재현 (지수를 처음부터 다시 계산할 때만)

### 3.1 환경
```bash
pip install -r requirements.txt      # pandas numpy pyreadstat networkx
```

### 3.2 API 키 (환경변수로만, 절대 커밋 금지)
| 키 | 용도 | 발급 |
|---|---|---|
| `TOURAPI_KEY` | 한국관광공사 TourAPI(관광지·맛집·축제) **필수** | data.go.kr / 한국관광콘텐츠랩(api.visitkorea.or.kr) |
| `DATAGO_KEY`  | 지역별 방문자수 API(쇠퇴지수 ①방문축) | data.go.kr 15101972 |

```bash
export TOURAPI_KEY="발급받은키"     # Windows(cmd): set TOURAPI_KEY=...
export DATAGO_KEY="발급받은키"
```

### 3.3 저장소에 없는 원본(라이선스·용량 사유, 별도 준비)
- `knts2025.sav` — 2025 국민여행조사 국내여행 원자료. 관광지식정보시스템(know.tour.go.kr)에서 받아 **저장소 루트에 배치**.
- `map/data/sigungu.geojson` — 시군구 경계(18MB). 아래로 재다운로드:
  ```bash
  curl -o map/data/sigungu.geojson \
    "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-municipalities-2018-geo.json"
  ```

### 3.4 실행 순서
```bash
python analysis/pull_visits.py           # ① 방문 (DATAGO_KEY 필요) → visits.json
python analysis/build_index.py           # ②③ (knts2025.sav 필요) → index_axes.json
python analysis/combine_index.py         # 복합쇠퇴지수 → index_full.json
python analysis/build_candidates.py      # 숨은매력지 후보 → candidates.json
python analysis/build_choropleth.py      # 단계구분도 geojson (sigungu.geojson 필요)
python analysis/build_service_data.py 12 # TourAPI 콘텐츠 (TOURAPI_KEY 필요) → momuri.json
```
> 이미 계산된 산출물이 저장소에 있으므로, **웹만 볼 거면 이 절차는 생략**해도 된다.

---

## 4. 현황 / 다음 할 일
- ✅ 파이프라인·3페이지 데모·밝은 테마·Jenks 단계구분도 완성
- ⬜ 테마 확장(미식 지수 등), 서비스명 확정, 축제(searchFestival2) 0건 이슈, 동선 연계 코스, 일자리(체류) 매칭
- 상세: [`docs/웹앱_기획_과제4.md`](docs/웹앱_기획_과제4.md) 12절

## 5. 데이터 출처
- 한국관광공사 TourAPI · 지역별 방문자수 API (data.go.kr / 한국관광콘텐츠랩)
- 국민여행조사(한국문화관광연구원) · 국가유산청 국가유산 검색 API
- 시군구 경계: southkorea/southkorea-maps (통계청 2018)
