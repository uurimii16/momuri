# -*- coding: utf-8 -*-
"""
한국관광공사 TourAPI 4.0(KorService2) 연동 모듈 + 단일 지역 콘텐츠 시연.
- 키는 환경변수 TOURAPI_KEY 로 전달(커밋 금지).
- 시군구명 → TourAPI sigunguCode 자동 해석 → 관광지/음식/축제 수집.
실행: TOURAPI_KEY=... python analysis/tourapi_fetch.py "경북" "상주시"
"""
import os, sys, json, datetime, urllib.request, urllib.parse

KEY = os.environ.get("TOURAPI_KEY", "").strip()
_TODAY = datetime.date.today()
TODAY = _TODAY.strftime("%Y%m%d")                                   # 조회일
YEAR_AGO = (_TODAY - datetime.timedelta(days=365)).strftime("%Y%m%d")  # 1년 전(연례 축제 포착용)
BASE = "http://apis.data.go.kr/B551011/KorService2"
# TourAPI 자체 지역코드(행정표준코드와 다름)
AREA = {"서울":1,"인천":2,"대전":3,"대구":4,"광주":5,"부산":6,"울산":7,"세종":8,
        "경기":31,"강원":32,"충북":33,"충남":34,"경북":35,"경남":36,"전북":37,"전남":38,"제주":39}

def api(op, **params):
    p = {"serviceKey":KEY,"MobileOS":"ETC","MobileApp":"momuri","_type":"json",
         "numOfRows":100,"pageNo":1}
    p.update(params)
    url = f"{BASE}/{op}?" + urllib.parse.urlencode(p)
    r = json.load(urllib.request.urlopen(url, timeout=60))
    body = r["response"]["body"]
    items = body.get("items")
    if not items or items == "": return []
    it = items.get("item", [])
    return it if isinstance(it, list) else [it]

def _query_fest(ac, sc):
    kw = dict(areaCode=ac, arrange="A", eventStartDate=YEAR_AGO)  # 최근 1년~예정 전부
    if sc is not None:
        kw["sigunguCode"] = sc
    return api("searchFestival2", **kw)

def _classify(items, scope):
    """각 축제에 scope(sigungu|sido)·status(upcoming|annual) 태깅.
    - upcoming: 종료일이 오늘 이후(진행/예정) → '지금 갈 이유'
    - annual : 이미 종료된 연례 축제(작년 일정) → 'N월 열리는 연례 축제'로 표기
    정렬: 예정(임박순) 먼저, 그다음 지난 축제(최근순)."""
    for x in items:
        x["scope"] = scope
        x["status"] = "upcoming" if (x.get("eventenddate") or "") >= TODAY else "annual"
    up = sorted([x for x in items if x["status"] == "upcoming"],
                key=lambda k: k.get("eventstartdate", ""))
    past = sorted([x for x in items if x["status"] == "annual"],
                  key=lambda k: k.get("eventstartdate", ""), reverse=True)
    return up + past

def fetch_festivals(ac, sc):
    """축제 조회 + 폴백.
    ⚠️ KorService2 특성(2026-07 확인): ①쇠퇴 소도시는 등록 축제가 거의 없음
    ②차년도 축제가 API에 늦게 반영됨 → '오늘 이후'만 조회하면 0건이 흔함.
    그래서 최근 1년 창으로 조회해 연례 축제까지 포착하고, 예정/연례를 구분 태깅한다.
    시군구 0건이면 도(道) 단위 인근 축제로 폴백."""
    local = _classify(_query_fest(ac, sc), "sigungu")
    if local:
        return local
    return _classify(_query_fest(ac, None), "sido")[:10]

def sigungu_code(area_code, name):
    for it in api("areaCode2", areaCode=area_code):
        if it["name"] == name or name.startswith(it["name"]):
            return it["code"]
    return None

def fetch_region(sido_s, sigungu):
    ac = AREA[sido_s]
    sc = sigungu_code(ac, sigungu)
    if sc is None:
        return {"error": f"sigunguCode 못 찾음: {sido_s} {sigungu}"}
    def pull(**kw):
        return api("areaBasedList2", areaCode=ac, sigunguCode=sc, arrange="O", **kw)
    spots   = pull(contentTypeId=12)  # 관광지
    culture = pull(contentTypeId=14)  # 문화시설(박물관·미술관·도서관·공연장)
    leports = pull(contentTypeId=28)  # 레포츠(등산·자전거·체험)
    shopping= pull(contentTypeId=38)  # 쇼핑(전통시장·로컬상점)
    foods   = pull(contentTypeId=39)  # 음식점(카페 포함 — cat3로 분리)
    stays   = pull(contentTypeId=32)  # 숙박(체류형 야간 스톱·한달살기)
    fests   = fetch_festivals(ac, sc) # 축제/행사(시군구 0건이면 도 단위 폴백)
    def slim(items):
        return [{"title":x.get("title"), "addr":x.get("addr1"),
                 "lng":x.get("mapx"), "lat":x.get("mapy"),
                 "img":x.get("firstimage"), "id":x.get("contentid"),
                 "cat3":x.get("cat3"), "tel":x.get("tel"),
                 "start":x.get("eventstartdate"), "end":x.get("eventenddate"),
                 "scope":x.get("scope"), "status":x.get("status")}
                for x in items]
    return {"sido":sido_s, "sigungu":sigungu, "areaCode":ac, "sigunguCode":sc,
            "spots":slim(spots), "culture":slim(culture),
            "leports":slim(leports), "shopping":slim(shopping),
            "foods":slim(foods), "stays":slim(stays), "festivals":slim(fests)}

if __name__ == "__main__":
    if not KEY:
        print("환경변수 TOURAPI_KEY 없음"); sys.exit(1)
    sido = sys.argv[1] if len(sys.argv) > 1 else "경북"
    sig  = sys.argv[2] if len(sys.argv) > 2 else "상주시"
    d = fetch_region(sido, sig)
    if d.get("error"): print(d["error"]); sys.exit(1)
    print(f"[{sido} {sig}] areaCode={d['areaCode']} sigunguCode={d['sigunguCode']}")
    print(f"  관광지 {len(d['spots'])} · 문화시설 {len(d['culture'])} · 음식 {len(d['foods'])} · 축제 {len(d['festivals'])}")
    print("\n  관광지 Top5:")
    for x in d["spots"][:5]:
        print(f"    - {x['title']}  ({x['lat']},{x['lng']})")
    print("  음식 Top5:")
    for x in d["foods"][:5]:
        print(f"    - {x['title']}")
    print("  축제(2026~):")
    for x in d["festivals"][:5]:
        print(f"    - {x['title']}  {x['start']}~{x['end']}")
