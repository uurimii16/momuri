# -*- coding: utf-8 -*-
"""
기존 decline_choropleth.geojson 후처리(원본 sigungu.geojson 재다운로드 불필요):
  ① candidates.json의 3축(ax_visit/ax_attract/ax_connect)을 properties에 조인
  ② shapely 단순화 + 좌표 정밀도 축소로 용량 대폭 감소(9MB→~1MB 목표)
  ③ UI에 필요한 속성만 남겨 슬림화
출력: map/data/decline_choropleth.geojson (덮어쓰기)
"""
import json
from shapely.geometry import shape, mapping

GEO = "map/data/decline_choropleth.geojson"
CANDS = "analysis/data/candidates.json"
TOL = 0.002          # 단순화 허용오차(도, ≈180m) — 전국 축척에서 형상 유지
PREC = 4             # 좌표 소수 자리

def round_coords(obj, p):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(obj[0], p), round(obj[1], p)]
        return [round_coords(x, p) for x in obj]
    return obj

def main():
    gj = json.load(open(GEO, encoding="utf-8"))
    cands = json.load(open(CANDS, encoding="utf-8"))

    # (시도약칭, 시군구명) → 3축
    lut = {}
    for c in cands:
        lut[(c["sido_s"], c["sigungu"])] = c

    matched = 0
    before_v = after_v = 0
    def count_v(x):
        if isinstance(x, list):
            if x and isinstance(x[0], (int, float)):
                return 1
            return sum(count_v(i) for i in x)
        return 0

    for f in gj["features"]:
        p = f["properties"]
        before_v += count_v(f["geometry"]["coordinates"])

        # ① 3축 조인
        c = lut.get((p.get("sido"), p.get("name")))
        if c:
            p["ax_visit"] = round(c["ax_visit"], 2)
            p["ax_attract"] = round(c["ax_attract"], 2)
            p["ax_connect"] = round(c["ax_connect"], 2)
            matched += 1

        # ③ 필요한 속성만 유지
        keep = {k: p[k] for k in ("name", "sido", "code", "composite", "level",
                                  "segment", "tier", "heritage", "hidden",
                                  "ax_visit", "ax_attract", "ax_connect") if k in p}
        f["properties"] = keep

        # ② 단순화 + 좌표 축소
        try:
            geom = shape(f["geometry"]).simplify(TOL, preserve_topology=True)
            f["geometry"] = mapping(geom)
        except Exception:
            pass
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"], PREC)
        after_v += count_v(f["geometry"]["coordinates"])

    json.dump(gj, open(GEO, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"features={len(gj['features'])}  3축 조인={matched}")
    print(f"정점 {before_v:,} → {after_v:,}  ({after_v/before_v*100:.0f}%)")

if __name__ == "__main__":
    main()
