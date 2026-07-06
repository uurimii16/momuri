# -*- coding: utf-8 -*-
"""
국가유산청 OpenAPI(무인증키)로 13개 활성화 타깃 도시의 '문화유산 루트'를 자동 생성한다.
출력: ../map/data/routes.json  (기존 창녕 flagship 루트는 유지하고 뒤에 13개를 추가)
- 목록 API: SearchKindOpenapiList.do  (등급/이름/시군구/좌표/ID)
- 이미지 API: SearchImageOpenapi.do    (사진 URL + 공공누리 imageNuri)
- 상세 API: SearchKindOpenapiDt.do      (소재지 주소 ccbaLcad)
"""
import json, math, time, re, urllib.request
from xml.etree import ElementTree as ET

BASE = "https://www.cha.go.kr/cha"
OUT = "../map/data/routes.json"

# (도시 표시명, 시도 ccbaCtcd, ccsiName 매칭 접두)
TARGETS = [
    ("충북 진천군", "33", "진천"),
    ("경북 울릉군", "37", "울릉"),
    ("경북 상주시", "37", "상주"),
    ("경기 의정부시", "31", "의정부"),
    ("경북 청송군", "37", "청송"),
    ("경기 여주시", "31", "여주"),
    ("경기 이천시", "31", "이천"),
    ("경북 경산시", "37", "경산"),
    ("충남 금산군", "34", "금산"),
    ("경남 거창군", "38", "거창"),
    ("경북 구미시", "37", "구미"),
    ("전남 함평군", "36", "함평"),
    ("경기 양평군", "31", "양평"),
]

GRADE = {"국보": 1, "보물": 2, "사적": 3, "사적및명승": 3, "명승": 4,
         "천연기념물": 5, "국가민속문화유산": 6, "국가등록문화유산": 7}
MAX_STOPS = 6

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
    _cache[code] = items
    return items

def haversine(a, b):
    R = 6371.0
    dlat = math.radians(b[1] - a[1]); dlng = math.radians(b[0] - a[0])
    s = (math.sin(dlat/2)**2 + math.cos(math.radians(a[1]))*math.cos(math.radians(b[1]))*math.sin(dlng/2)**2)
    return 2 * R * math.asin(math.sqrt(s))

def get_image(kdcd, asno, ctcd):
    xml = fetch(f"{BASE}/SearchImageOpenapi.do?ccbaKdcd={kdcd}&ccbaAsno={asno}&ccbaCtcd={ctcd}")
    m = re.search(r"<imageUrl>(.*?)</imageUrl>", xml)
    return (m.group(1).strip().replace("http://", "https://")) if m else ""

def _clean(s):
    return re.sub(r"<!\[CDATA\[|\]\]>", "", s or "").strip()

def get_address(kdcd, asno, ctcd):
    xml = fetch(f"{BASE}/SearchKindOpenapiDt.do?ccbaKdcd={kdcd}&ccbaAsno={asno}&ccbaCtcd={ctcd}")
    for tag in ("ccbaLcad", "ccbaLcto"):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", xml, re.S)
        if m and _clean(m.group(1)):
            return _clean(m.group(1))
    return ""

def order_route(stops):
    """최고 등급을 시작점으로 최근접 이웃 정렬(지그재그 완화)."""
    if len(stops) <= 2:
        return stops
    remaining = stops[:]
    route = [remaining.pop(0)]
    while remaining:
        last = (route[-1]["lng"], route[-1]["lat"])
        remaining.sort(key=lambda s: haversine(last, (s["lng"], s["lat"])))
        route.append(remaining.pop(0))
    return route

def build_city(name, code, prefix):
    items = list_sido(code)
    picked = []
    for it in items:
        if not txt(it, "ccsiName").startswith(prefix):
            continue
        lng, lat = txt(it, "longitude"), txt(it, "latitude")
        try:
            lng, lat = float(lng), float(lat)
        except ValueError:
            continue
        if not (124 < lng < 132 and 33 < lat < 39):
            continue
        picked.append({
            "grade": GRADE.get(txt(it, "ccmaName"), 9),
            "kind": txt(it, "ccmaName"),
            "name": txt(it, "ccbaMnm1"),
            "kdcd": txt(it, "ccbaKdcd"), "asno": txt(it, "ccbaAsno"), "ctcd": txt(it, "ccbaCtcd"),
            "lng": lng, "lat": lat,
        })
    # 등급 우선 + 중복 좌표 제거
    picked.sort(key=lambda s: s["grade"])
    seen, uniq = set(), []
    for s in picked:
        key = (round(s["lng"], 4), round(s["lat"], 4))
        if key in seen:
            continue
        seen.add(key); uniq.append(s)
        if len(uniq) >= MAX_STOPS:
            break
    if len(uniq) < 2:
        print(f"  ! {name}: 좌표 유효 유산 {len(uniq)}건 → 건너뜀")
        return None
    route = order_route(uniq)
    # 사진/주소 채우기
    waypoints, path = [], []
    for i, s in enumerate(route, 1):
        img = get_image(s["kdcd"], s["asno"], s["ctcd"])
        addr = get_address(s["kdcd"], s["asno"], s["ctcd"]) or f"{name} · {s['kind']}"
        path.append([s["lng"], s["lat"]])
        waypoints.append({
            "id": f"{prefix}-{i}",
            "name": s["name"],
            "address": addr,
            "fallbackLat": s["lat"], "fallbackLng": s["lng"],
            "lockCoordinates": True,
            "category": s["kind"],
            "stay": "40분",
            "imageUrl": img,
            "description": f"{name} 활성화 타깃의 대표 {s['kind']}. 데이터 진단 기반 문화유산 추천 동선의 거점.",
        })
        print(f"    {i}. {s['name']} ({s['kind']}) 사진{'O' if img else 'X'}")
        time.sleep(0.15)
    dist_km = sum(haversine(path[i], path[i+1]) for i in range(len(path)-1)) * 1.3
    dur_s = int(dist_km / 40 * 3600) + len(waypoints) * 40 * 60
    kinds = [w["category"] for w in waypoints]
    theme = " · ".join(dict.fromkeys(kinds[:3]))
    return {
        "id": f"{prefix}-heritage",
        "title": f"{name.split()[-1]} 국가유산 루트",
        "region": name,
        "creator": "관광쇠퇴 진단 기반 자동 큐레이션",
        "theme": theme,
        "distance": f"약 {round(dist_km)}km",
        "routeDistanceMeters": int(dist_km * 1000),
        "duration": f"약 {round(dur_s/3600, 1)}시간",
        "routeDurationSeconds": dur_s,
        "difficulty": "보통",
        "description": f"복합 관광쇠퇴지수상 활성화 타깃인 {name.split()[-1]}. 국가유산청 지정유산을 등급·거리 기준으로 이은 데이터 기반 추천 동선(출처: 국가유산청).",
        "routePath": path,
        "waypoints": waypoints,
    }

def enrich_flagship(course, code):
    """큐레이션된 창녕 루트의 각 지점에 이름 매칭으로 사진·주소를 채운다."""
    idx = {}
    for it in list_sido(code):
        idx[txt(it, "ccbaMnm1")] = (txt(it, "ccbaKdcd"), txt(it, "ccbaAsno"), txt(it, "ccbaCtcd"))
    for w in course.get("waypoints", []):
        ids = idx.get(w["name"])
        if not ids:
            continue
        img = get_image(*ids)
        addr = get_address(*ids)
        if img:
            w["imageUrl"] = img
        if addr:
            w["address"] = addr
        print(f"    · {w['name']} 사진{'O' if img else 'X'}")
        time.sleep(0.15)
    return course

def main():
    with open(OUT, encoding="utf-8") as f:
        existing = json.load(f)
    flagship = [c for c in existing if c.get("id") == "changnyeong-heritage"]
    print("[flagship 창녕 사진·주소 보강]")
    for c in flagship:
        enrich_flagship(c, "38")

    courses = list(flagship)
    for name, code, prefix in TARGETS:
        print(f"[{name}]")
        c = build_city(name, code, prefix)
        if c:
            courses.append(c)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=1)
    print(f"\n완료: 총 {len(courses)}개 루트 → {OUT}")

if __name__ == "__main__":
    main()
