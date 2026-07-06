# -*- coding: utf-8 -*-
"""
시군구 경계 GeoJSON + 복합쇠퇴지수 → 단계구분도용 경량 GeoJSON.
- 좌표 정밀도 4자리로 축소(형상 유지, 용량↓)
- candidates.json의 composite/tier/segment 를 (시도,시군구명)으로 조인
- 5단계 분위(quantile) level 부여
출력: map/data/decline_choropleth.geojson
"""
import json, os, bisect

FULL = "map/data/sigungu.geojson"
CANDS = "analysis/data/candidates.json"
OUT = "map/data/decline_choropleth.geojson"

# 통계청(KOSTAT) 시도코드 앞2자리 → 시도약칭 (이 GeoJSON이 쓰는 코드체계)
PREF = {"11":"서울","21":"부산","22":"대구","23":"인천","24":"광주","25":"대전","26":"울산",
        "29":"세종","31":"경기","32":"강원","33":"충북","34":"충남","35":"전북","36":"전남",
        "37":"경북","38":"경남","39":"제주"}

def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [round_coords(x) for x in c]

def main():
    full = json.load(open(FULL, encoding="utf-8"))
    cands = json.load(open(CANDS, encoding="utf-8"))
    look = {(c["sido_s"], c["sigungu"]): c for c in cands}

    comps = sorted(c["composite"] for c in cands)
    qs = [comps[int(len(comps) * p)] for p in (0.2, 0.4, 0.6, 0.8)]
    def level(v): return bisect.bisect_right(qs, v) + 1   # 1(낮음)~5(쇠퇴심함)

    feats, matched = [], 0
    for f in full["features"]:
        p = f["properties"]; code = str(p.get("code", "")); sido = PREF.get(code[:2], "")
        c = look.get((sido, p.get("name")))
        props = {"name": p.get("name"), "sido": sido, "code": code}
        if c:
            matched += 1
            props.update(composite=round(c["composite"], 2), tier=c["tier"],
                         segment=c["segment"], level=level(c["composite"]),
                         hidden=round(c["hidden_score"], 2), heritage=c["heritage"])
        else:
            props.update(composite=None, level=0)
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})

    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"저장: {OUT}  용량 {os.path.getsize(OUT)/1e6:.1f}MB")
    print(f"경계 {len(feats)}개 중 지수 조인 {matched}개 (도지역 시군)")
    print(f"5단계 분위 경계값: {[round(q,2) for q in qs]}")

if __name__ == "__main__":
    main()
