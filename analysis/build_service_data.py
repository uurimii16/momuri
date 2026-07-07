# -*- coding: utf-8 -*-
"""
[Phase 1-3] 숨은매력지 후보 + TourAPI 콘텐츠 → 지도 서비스 데이터(momuri.json).
- candidates.json에서 tier=target & 숨은매력지 상위 N개
- 각 지역의 관광지/음식/축제를 TourAPI로 수집, 좌표 있는 것만 스톱으로
- 지역 대표좌표 = 스톱 좌표 평균(centroid)
실행: TOURAPI_KEY=... python analysis/build_service_data.py [N]
"""
import os, sys, json
from tourapi_fetch import fetch_region

TOP_N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
OUT = "map/data/momuri.json"

def with_coord(items, k=8):
    out = []
    for x in items:
        try:
            lng, lat = float(x["lng"]), float(x["lat"])
        except (TypeError, ValueError):
            continue
        if lng and lat:
            item = {"title":x["title"], "addr":x["addr"], "lat":lat, "lng":lng,
                    "img":x["img"], "start":x.get("start"), "end":x.get("end")}
            if x.get("scope"): item["scope"] = x["scope"]    # 축제: 'sido'면 인근 축제
            if x.get("status"): item["status"] = x["status"] # 축제: upcoming|annual(연례)
            out.append(item)
        if len(out) >= k: break
    return out

def main():
    cands = json.load(open("analysis/data/candidates.json", encoding="utf-8"))
    picks = [c for c in cands if c["tier"] == "target"
             and c["segment"] == "숨은매력지(문화유산형)"][:TOP_N]
    print(f"대상 {len(picks)}곳: {[p['sigungu'] for p in picks]}")

    result = []
    for c in picks:
        d = fetch_region(c["sido_s"], c["sigungu"])
        if d.get("error"):
            print("  스킵:", c["region"], d["error"]); continue
        spots = with_coord(d["spots"], 8)
        foods = with_coord(d["foods"], 5)
        stays = with_coord(d.get("stays", []), 6)   # 체류형 야간 스톱·한달살기 숙소
        fests = with_coord(d["festivals"], 5)
        allpts = spots + foods
        if not allpts:
            print("  좌표없음 스킵:", c["region"]); continue
        clat = sum(p["lat"] for p in allpts) / len(allpts)
        clng = sum(p["lng"] for p in allpts) / len(allpts)
        result.append({
            "region": c["region"], "sido": c["sido_s"], "sigungu": c["sigungu"],
            "theme": c["theme"], "segment": c["segment"],
            "composite": round(c["composite"], 2), "hidden_score": round(c["hidden_score"], 2),
            "heritage": c["heritage"],
            "axes": {"visit":round(c["ax_visit"],1),"attract":round(c["ax_attract"],1),"connect":round(c["ax_connect"],1)},
            "lat": round(clat, 6), "lng": round(clng, 6),
            "spots": spots, "foods": foods, "stays": stays, "festivals": fests,
        })
        print(f"  ✓ {c['region']:14s} 관광지{len(spots)}·음식{len(foods)}·숙박{len(stays)}·축제{len(fests)}")

    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT} ({len(result)}곳)")

if __name__ == "__main__":
    main()
