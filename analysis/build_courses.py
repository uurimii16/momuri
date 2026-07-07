# -*- coding: utf-8 -*-
"""
숨은 매력지별 '체류 코스' 생성 — 하루 코스 + 다일(체류형) 코스.
- 입력: map/data/momuri.json (지역별 spots/foods/stays, 좌표·사진·주소)
- 하루 골격: 명소→점심맛집→명소→명소→저녁맛집 (5스톱), 매 단계 직전 위치 최근접 미사용 스톱(그리디 = 현실적 동선)
- 다일: 같은 그리디를 스톱 풀을 날짜 간 공유 소비하며 최대 MAX_DAYS일 반복
        → 날마다 다른 장소, 마지막 날 빼고 야간=stays[] 최근접 장기 숙소.
        (과제4 '체류형 로컬 관광 플래너' 핵심: 워케이션·한달살기)
- 자동차 구간: OSRM 공개서버(무료, 키 불필요) — 구간별 소요분·거리·실제 도로 경로선
- 대중교통 구간: ODsay API — 환경변수 ODSAY_KEY 있을 때만 채움. 없으면 transit=null
- 하위호환: 최상위 stops/legs/stay_total_min = Day1(기존 course.html 그대로 동작). 다일은 days[].
출력: map/data/courses.json
실행:  python analysis/build_courses.py                    # 자동차만
       ODSAY_KEY=발급키 python analysis/build_courses.py   # 대중교통까지
"""
import json, os, time, math, subprocess, urllib.request, urllib.parse

SRC = "map/data/momuri.json"
OUT = "map/data/courses.json"
OSRM = "https://router.project-osrm.org/route/v1/driving"
ODSAY_KEY = os.environ.get("ODSAY_KEY", "").strip()
# ODsay 앱에 등록한 '서비스 URL(허용 도메인)'과 동일하게. 서버측 호출이라 이 값을 Referer로 붙여 도메인검증 통과.
ODSAY_REFERER = os.environ.get("ODSAY_REFERER", "https://momuri.netlify.app").strip()

MAX_DAYS = 3   # 데이터(명소8+맛집5)로 현실적인 상한. 한달살기는 프론트에서 '반복+탐색'으로 확장 프레이밍.
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

def loc(s):
    return [s["lng"], s["lat"]]

def pick_day(spots, foods, cur):
    """PLAN 골격대로 최근접 그리디 선택(풀에서 소비). 시작=cur. 반환:(stops, 새 cur)."""
    stops = []
    for kind, stay in PLAN:
        cand = spots if kind == "명소" else foods
        if not cand:
            continue
        nxt = min(cand, key=lambda s: haversine(cur, loc(s)))
        cand.remove(nxt)
        stops.append({"kind": kind, "name": nxt["title"], "addr": nxt.get("addr", ""),
                      "lat": nxt["lat"], "lng": nxt["lng"], "img": nxt.get("img", ""), "stay": stay})
        cur = loc(nxt)
    return stops, cur

def build_days(region):
    """스톱 풀을 날짜 간 공유 소비하며 다일 코스 구성. 야간=최근접 장기 숙소(마지막 날 제외)."""
    spots = [dict(s) for s in region["spots"] if s.get("lat")]
    foods = [dict(s) for s in region["foods"] if s.get("lat")]
    stays = [dict(s) for s in region.get("stays", []) if s.get("lat")]
    cur = [region["lng"], region["lat"]]
    days = []
    for d in range(1, MAX_DAYS + 1):
        day_stops, cur = pick_day(spots, foods, cur)
        if len(day_stops) < 2:
            break
        days.append({"day": d, "stops": day_stops})
    # 야간 숙소 배정: 마지막 날은 체크아웃(야간 없음), 그 외는 그날 마지막 스톱 최근접 숙소
    for i, day in enumerate(days):
        if i == len(days) - 1:
            day["night"] = None
            continue
        last = loc(day["stops"][-1])
        if stays:
            nx = min(stays, key=lambda s: haversine(last, loc(s)))
            stays.remove(nx)
            day["night"] = {"kind": "숙박", "name": nx["title"], "addr": nx.get("addr", ""),
                            "lat": nx["lat"], "lng": nx["lng"], "img": nx.get("img", "")}
            cur = loc(nx)  # 다음날은 숙소에서 출발(이미 pick_day가 소비해 순서엔 영향 없지만 의미 명확화)
        else:
            day["night"] = None
    return days

def leg_between(a, b):
    lg = {"car": osrm_leg(a, b), "transit": odsay_leg(a, b)}
    time.sleep(0.4)   # 공개서버 예의
    return lg

def build_day_legs(day):
    """하루 안 스톱 간 이동 + (야간 있으면) 마지막 스톱→숙소 이동."""
    stops = day["stops"]
    legs = []
    for i in range(len(stops) - 1):
        legs.append(leg_between(loc(stops[i]), loc(stops[i+1])))
    day["legs"] = legs
    day["to_night"] = leg_between(loc(stops[-1]), loc(day["night"])) if day.get("night") else None
    day["car_total_min"] = sum(l["car"]["min"] for l in legs) + (day["to_night"]["car"]["min"] if day["to_night"] else 0)
    day["stay_total_min"] = sum(s["stay"] for s in stops)
    return day

def main():
    regions = json.load(open(SRC, encoding="utf-8"))
    out = []
    for r in regions:
        days = build_days(r)
        if not days:
            continue
        for day in days:
            build_day_legs(day)
        d1 = days[0]                      # 하위호환용 Day1
        n_nights = sum(1 for d in days if d.get("night"))
        course = {
            "region": r["region"], "sido": r["sido"], "sigungu": r["sigungu"],
            "theme": r["theme"], "composite": r["composite"], "heritage": r["heritage"],
            "center": [r["lng"], r["lat"]],
            # --- 하위호환(course.html): 최상위 = Day1 ---
            "stops": d1["stops"], "legs": d1["legs"],
            "car_total_min": d1["car_total_min"],
            "stay_total_min": d1["stay_total_min"],
            "has_transit": all(l["transit"] for l in d1["legs"]) if d1["legs"] else False,
            # --- 다일 체류(stay.html) ---
            "days": days,
            "n_days": len(days),
            "n_nights": n_nights,
            "has_stay_data": n_nights > 0,
        }
        out.append(course)
        tot = sum(d["car_total_min"] for d in days)
        stay_lbl = f"{n_nights}박" if n_nights else "숙소0(인근안내)"
        print(f"  {r['region']:16s} {len(days)}일 · {stay_lbl} · 자동차 총 {tot}분")
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"\n저장: {OUT}  ({len(out)}개 코스, {os.path.getsize(OUT)/1024:.0f}KB)")
    if not ODSAY_KEY:
        print("※ 대중교통은 미포함. `ODSAY_KEY=발급키 python analysis/build_courses.py`로 재생성하면 채워집니다.")

if __name__ == "__main__":
    main()
