# -*- coding: utf-8 -*-
"""
국가유산청 OpenAPI(무인증)로 momuri.json 12개 숨은매력지의 '국가지정 유산 목록'을 수집한다.
출력: ../map/data/heritage.json  = { "시군구명": [ {"n":이름,"k":종목,"g":등급,"la":위도,"lo":경도}, ... ] }
- 목록 API: SearchKindOpenapiList.do?ccbaCtcd={시도코드}  (등급/이름/시군구/좌표)
※ SearchKindOpenapiList는 국가지정+국가등록만 반환(시도지정 제외) → '국가지정 유산'으로 표기.
실행: python analysis/build_heritage.py   (analysis 폴더 밖에서 실행해도 됨)
"""
import json, time, os, urllib.request
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.cha.go.kr/cha"
MOMURI = os.path.join(HERE, "..", "map", "data", "momuri.json")
OUT    = os.path.join(HERE, "..", "map", "data", "heritage.json")

# 국가유산청 시도코드(행정코드와 다름)
SIDO2CTCD = {
    "서울":"11","부산":"21","대구":"22","인천":"23","광주":"24","대전":"25","울산":"26","세종":"45",
    "경기":"31","강원":"32","충북":"33","충남":"34","전북":"35","전남":"36","경북":"37","경남":"38","제주":"50",
}
GRADE = {"국보":1,"보물":2,"사적":3,"사적및명승":3,"명승":4,
         "천연기념물":5,"국가민속문화유산":6,"국가등록문화유산":7}

def fetch(url, tries=4):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if a == tries - 1:
                return ""
            time.sleep(2)
    return ""

def txt(item, tag):
    e = item.find(tag)
    return (e.text or "").strip() if e is not None and e.text else ""

def list_sido(code, _cache={}):
    if code in _cache:
        return _cache[code]
    items, page = [], 1
    while True:
        xml = fetch(f"{BASE}/SearchKindOpenapiList.do?ccbaCtcd={code}&pageUnit=990&pageIndex={page}&ccbaCncl=N")
        if not xml:
            break
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            break
        page_items = root.findall("item")
        items.extend(page_items)
        total = int((root.findtext("totalCnt") or "0"))
        if len(items) >= total or not page_items:
            break
        page += 1
        time.sleep(0.2)
    _cache[code] = items
    return items

def prefix_of(sigungu):
    """'진천군'→'진천', '여주시'→'여주' (시군구 접미어 제거해 ccsiName 접두 매칭)."""
    s = (sigungu or "").strip()
    return s[:-1] if s and s[-1] in "시군구" else s

def collect(sido, sigungu):
    code = SIDO2CTCD.get((sido or "").strip())
    if not code:
        return []
    pre = prefix_of(sigungu)
    out, seen = [], set()
    for it in list_sido(code):
        if not txt(it, "ccsiName").startswith(pre):
            continue
        try:
            lng, lat = float(txt(it, "longitude")), float(txt(it, "latitude"))
        except ValueError:
            continue
        if not (124 < lng < 132 and 33 < lat < 39):   # 0,0 등 무효좌표 제외
            continue
        key = (round(lng, 4), round(lat, 4))
        if key in seen:
            continue
        seen.add(key)
        kind = txt(it, "ccmaName")
        out.append({"n": txt(it, "ccbaMnm1"), "k": kind,
                    "g": GRADE.get(kind, 9), "la": round(lat, 6), "lo": round(lng, 6)})
    out.sort(key=lambda s: (s["g"], s["n"]))   # 국보·보물 우선
    return out

def main():
    regions = json.load(open(MOMURI, encoding="utf-8"))
    result = {}
    for r in regions:
        lst = collect(r.get("sido"), r.get("sigungu"))
        result[r["sigungu"]] = lst
        r["heritage_mapped"] = len(lst)          # 지도표시 가능 국가지정 건수
        print(f"  {r['region']:16s} 국가지정 {len(lst):>3d}건 (밀도값 {r.get('heritage')})")
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(regions, open(MOMURI, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(len(v) for v in result.values())
    print(f"\n완료: {len(result)}개 지역 · 국가지정 유산 총 {total}건 → {OUT}")
    print(f"      momuri.json에 heritage_mapped 필드 갱신")

if __name__ == "__main__":
    main()
