# -*- coding: utf-8 -*-
"""
시군구 경계 GeoJSON + 복합쇠퇴지수 → 단계구분도용 경량 GeoJSON.
- 좌표 정밀도 4자리로 축소(형상 유지, 용량↓)
- candidates.json의 composite/tier/segment 를 (시도,시군구명)으로 조인
- 5단계 Jenks natural breaks(자연분류)로 level 부여 + 구간 경계값 출력
출력: map/data/decline_choropleth.geojson, map/data/decline_breaks.json
"""
import json, os

FULL = "map/data/sigungu.geojson"
CANDS = "analysis/data/candidates.json"
OUT = "map/data/decline_choropleth.geojson"
BREAKS_OUT = "map/data/decline_breaks.json"

# 통계청(KOSTAT) 시도코드 앞2자리 → 시도약칭 (이 GeoJSON이 쓰는 코드체계)
PREF = {"11":"서울","21":"부산","22":"대구","23":"인천","24":"광주","25":"대전","26":"울산",
        "29":"세종","31":"경기","32":"강원","33":"충북","34":"충남","35":"전북","36":"전남",
        "37":"경북","38":"경남","39":"제주"}

def jenks_breaks(values, nb_class):
    """Jenks natural breaks — 클래스 내 분산 최소화. 반환: nb_class+1개 경계(최소~최대)."""
    values = sorted(values)
    n = len(values)
    mat1 = [[0]*(nb_class+1) for _ in range(n+1)]
    mat2 = [[0]*(nb_class+1) for _ in range(n+1)]
    for i in range(1, nb_class+1):
        mat1[1][i] = 1
        for j in range(2, n+1):
            mat2[j][i] = float("inf")
    for l in range(2, n+1):
        s1 = s2 = w = 0.0
        for m in range(1, l+1):
            i3 = l - m + 1
            val = values[i3-1]
            s2 += val*val; s1 += val; w += 1
            v = s2 - (s1*s1)/w
            i4 = i3 - 1
            if i4 != 0:
                for j in range(2, nb_class+1):
                    if mat2[l][j] >= (v + mat2[i4][j-1]):
                        mat1[l][j] = i3
                        mat2[l][j] = v + mat2[i4][j-1]
        mat1[l][1] = 1
        mat2[l][1] = s2 - (s1*s1)/w
    k = n
    kclass = [0.0]*(nb_class+1)
    kclass[nb_class] = values[-1]
    kclass[0] = values[0]
    for j in range(nb_class, 1, -1):
        idx = int(mat1[k][j]) - 2
        kclass[j-1] = values[idx]
        k = int(mat1[k][j]) - 1
    return kclass

def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [round_coords(x) for x in c]

SIMP_TOL = 0.002   # 단순화 허용오차(도, ≈180m) — 전국 축척 형상 유지, 용량↓
def simplify_geom(geom):
    """shapely 있으면 Douglas-Peucker 단순화(용량 9MB→~0.7MB). 없으면 원형 유지."""
    try:
        from shapely.geometry import shape, mapping
        return mapping(shape(geom).simplify(SIMP_TOL, preserve_topology=True))
    except Exception:
        return geom

def main():
    full = json.load(open(FULL, encoding="utf-8"))
    cands = json.load(open(CANDS, encoding="utf-8"))
    look = {(c["sido_s"], c["sigungu"]): c for c in cands}

    comps = [c["composite"] for c in cands]
    breaks = jenks_breaks(comps, 5)   # 6개 경계값
    def level(v):
        for i in range(1, len(breaks)):
            if v <= breaks[i]:
                return i
        return len(breaks) - 1

    feats, matched = [], 0
    for f in full["features"]:
        p = f["properties"]; code = str(p.get("code", "")); sido = PREF.get(code[:2], "")
        c = look.get((sido, p.get("name")))
        props = {"name": p.get("name"), "sido": sido, "code": code}
        if c:
            matched += 1
            props.update(composite=round(c["composite"], 2), tier=c["tier"],
                         segment=c["segment"], level=level(c["composite"]),
                         hidden=round(c["hidden_score"], 2), heritage=c["heritage"],
                         ax_visit=round(c["ax_visit"], 2), ax_attract=round(c["ax_attract"], 2),
                         ax_connect=round(c["ax_connect"], 2))
        else:
            props.update(composite=None, level=0)
        f["geometry"] = simplify_geom(f["geometry"])
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})

    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"method": "Jenks natural breaks", "n": len(comps),
               "breaks": [round(b, 2) for b in breaks]},
              open(BREAKS_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: {OUT}  용량 {os.path.getsize(OUT)/1e6:.1f}MB")
    print(f"경계 {len(feats)}개 중 지수 조인 {matched}개 (도지역 시군)")
    print(f"Jenks 5단계 경계값: {[round(b,2) for b in breaks]}")
    dist = {}
    for f in feats:
        lv = f["properties"]["level"]
        if lv: dist[lv] = dist.get(lv, 0) + 1
    print(f"단계별 시군 수: {dict(sorted(dist.items()))}")

if __name__ == "__main__":
    main()
