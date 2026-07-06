# -*- coding: utf-8 -*-
"""
숨은 매력지별 '하루 코스'(명소·맛집 섞은 데이트/여행 동선) 생성.
- 입력: map/data/momuri.json (지역별 spots/foods, 좌표·사진·주소)
- 구성: 명소→점심맛집→명소→명소→저녁맛집 (5스톱), 각 단계 직전 위치에서 가장 가까운 미사용 스톱을 선택(그리디 최근접 = 현실적 동선)
- 자동차 구간: OSRM 공개서버(무료, 키 불필요) — 구간별 소요분·거리·실제 도로 경로선
- 대중교통 구간: ODsay API — 환경변수 ODSAY_KEY 있을 때만 채움(버스번호·환승·소요분). 없으면 transit=null
출력: map/data/courses.json
실행:  python analysis/build_courses.py              # 자동차만
       ODSAY_KEY=발급키 python analysis/build_courses.py   # 대중교통까지
"""
import json, os, time, math, subprocess, urllib.request, urllib.parse

SRC = "map/data/momuri.json"
OUT = "map/data/courses.json"
OSRM = "https://router.project-osrm.org/route/v1/driving"
ODSAY_KEY = os.environ.get("ODSAY_KEY", "").strip()
# ODsay 앱에 등록한 '서비스 URL(허용 도메인)'과 동일하게. 서버측 호출이라 이 값을 Referer로 붙여 도메인검증 통과.
ODSAY_REFERER = os.environ.get("ODSAY_REFERER", "https://momuri.netlify.app").strip()

# 하루 코스 골격: (종류, 머무는 분). 앞에서부터 직전 위치 최근접으로 채움
PLAN = [("명소", 80), ("맛집", 60), ("명소", 80), ("명소", 60), ("맛집", 70)]

def haversine(a, b):
    R = 6371.0
    dlat = math.radians(b[1]-a[1]); dlng = math.radians(b[0]-a[0])
    h = math.sin(dlat/2)**2 + math.cos(math.radians(a[1]))*math.cos(math.radians(b[1]))*math.sin(dlng/2)**2
    return 2*R*math.asin(math.sqrt(h))

def get(url, tries=3, use_curl=False, referer=None):
    """공개 API GET → dict. OSRM 데모서버는 urllib TLS를 막아 curl로 우회(use_curl).
    referer: ODsay 도메인검증용 Referer 헤더(서버측 호출엔 referer가 없어 붙여줌)."""
    for i in range(tries):
        try:
            if use_curl:
                cmd = ["curl", "-s", "--max-time", "25", "-A", "momuri-course/1.0"]
                if referer:
                    cmd += ["-e", referer]
                out = subprocess.run(cmd + [url], capture_output=True, text=True, timeout=30).stdout
                return json.loads(out) if out.strip() else None
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.load(r)
        except Exception:
            if i == tries-1:
                return None
            time.sleep(1.5)
    return None

def osrm_leg(a, b):
    """a,b=[lng,lat] → {min,km,path}. 실패시 하버사인 추정."""
    url = f"{OSRM}/{a[0]},{a[1]};{b[0]},{b[1]}?overview=full&geometries=geojson"
    d = get(url, use_curl=True)
    if d and d.get("code") == "Ok" and d.get("routes"):
        r = d["routes"][0]
        return {"min": round(r["duration"]/60), "km": round(r["distance"]/1000, 1),
                "path": [[round(x, 5), round(y, 5)] for x, y in r["geometry"]["coordinates"]]}
    km = haversine(a, b)
    return {"min": round(km/40*60), "km": round(km, 1), "path": [a, b], "estimated": True}

def odsay_leg(a, b):
    """ODsay 대중교통 최적경로 → {min,transfers,steps}. 키 없거나 실패시 None."""
    if not ODSAY_KEY:
        return None
    q = urllib.parse.urlencode({"SX": a[0], "SY": a[1], "EX": b[0], "EY": b[1],
                                "apiKey": ODSAY_KEY, "OPT": 0})
    d = get(f"https://api.odsay.com/v1/api/searchPubTransPathT?{q}", use_curl=True, referer=ODSAY_REFERER)
    try:
        path = d["result"]["path"][0]
        info = path["info"]
        TT = {1: "지하철", 2: "버스", 3: "도보"}
        steps = []
        for sp in path["subPath"]:
            t = sp.get("trafficType")
            if t == 3:
                if sp.get("sectionTime"):
                    steps.append({"type": "도보", "min": sp["sectionTime"]})
                continue
            lane = (sp.get("lane") or [{}])[0]
            name = lane.get("busNo") or lane.get("name") or ""
            steps.append({"type": TT.get(t, "대중"), "name": name,
                          "min": sp.get("sectionTime", 0),
                          "from": sp.get("startName", ""), "to": sp.get("endName", ""),
                          "stations": sp.get("stationCount")})
        return {"min": round(info["totalTime"]), "transfers": info.get("busTransitCount", 0)+info.get("subwayTransitCount", 0),
                "walk_min": round(info.get("totalWalkTime", 0)), "steps": steps}
    except Exception:
        return None

def build_stops(region):
    """PLAN 골격대로 최근접 그리디 선택. 시작점=지역 중심."""
    pool = {"명소": [dict(s, kind="명소") for s in region["spots"] if s.get("lat")],
            "맛집": [dict(s, kind="맛집") for s in region["foods"] if s.get("lat")]}
    cur = [region["lng"], region["lat"]]
    stops = []
    for kind, stay in PLAN:
        cand = pool.get(kind, [])
        if not cand:
            continue
        nxt = min(cand, key=lambda s: haversine(cur, [s["lng"], s["lat"]]))
        cand.remove(nxt)
        stops.append({"kind": kind, "name": nxt["title"], "addr": nxt.get("addr", ""),
                      "lat": nxt["lat"], "lng": nxt["lng"], "img": nxt.get("img", ""), "stay": stay})
        cur = [nxt["lng"], nxt["lat"]]
    return stops

def main():
    regions = json.load(open(SRC, encoding="utf-8"))
    out = []
    for r in regions:
        stops = build_stops(r)
        if len(stops) < 2:
            continue
        legs = []
        for i in range(len(stops)-1):
            a = [stops[i]["lng"], stops[i]["lat"]]
            b = [stops[i+1]["lng"], stops[i+1]["lat"]]
            legs.append({"car": osrm_leg(a, b), "transit": odsay_leg(a, b)})
            time.sleep(0.4)   # 공개서버 예의
        out.append({
            "region": r["region"], "sido": r["sido"], "sigungu": r["sigungu"],
            "theme": r["theme"], "composite": r["composite"], "heritage": r["heritage"],
            "center": [r["lng"], r["lat"]],
            "stops": stops, "legs": legs,
            "car_total_min": sum(l["car"]["min"] for l in legs),
            "stay_total_min": sum(s["stay"] for s in stops),
            "has_transit": all(l["transit"] for l in legs) if legs else False,
        })
        n_tr = sum(1 for l in legs if l["transit"])
        tr_lbl = "O(전구간)" if out[-1]["has_transit"] else (f"△({n_tr}/{len(legs)}구간)" if n_tr else ("X(경로없음)" if ODSAY_KEY else "X(키없음)"))
        print(f"  {r['region']:16s} 스톱 {len(stops)} · 자동차 {out[-1]['car_total_min']}분 · 대중교통 {tr_lbl}")
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"\n저장: {OUT}  ({len(out)}개 코스, {os.path.getsize(OUT)/1024:.0f}KB)")
    if not ODSAY_KEY:
        print("※ 대중교통은 미포함. `ODSAY_KEY=발급키 python analysis/build_courses.py`로 재생성하면 채워집니다.")

if __name__ == "__main__":
    main()
