# -*- coding: utf-8 -*-
"""
한국관광공사 TourAPI 4.0(KorService2) 연동 모듈 + 단일 지역 콘텐츠 시연.
- 키는 환경변수 TOURAPI_KEY 로 전달(커밋 금지).
- 시군구명 → TourAPI sigunguCode 자동 해석 → 관광지/음식/축제 수집.
실행: TOURAPI_KEY=... python analysis/tourapi_fetch.py "경북" "상주시"
"""
import os, sys, json, urllib.request, urllib.parse

KEY = os.environ.get("TOURAPI_KEY", "").strip()
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
    spots = pull(contentTypeId=12)   # 관광지
    culture = pull(contentTypeId=14) # 문화시설
    foods = pull(contentTypeId=39)   # 음식점
    fests = api("searchFestival2", areaCode=ac, sigunguCode=sc,
                arrange="O", eventStartDate="20260101")  # 축제/행사
    def slim(items):
        return [{"title":x.get("title"), "addr":x.get("addr1"),
                 "lng":x.get("mapx"), "lat":x.get("mapy"),
                 "img":x.get("firstimage"), "id":x.get("contentid"),
                 "start":x.get("eventstartdate"), "end":x.get("eventenddate")}
                for x in items]
    return {"sido":sido_s, "sigungu":sigungu, "areaCode":ac, "sigunguCode":sc,
            "spots":slim(spots), "culture":slim(culture),
            "foods":slim(foods), "festivals":slim(fests)}

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
