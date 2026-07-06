# -*- coding: utf-8 -*-
"""
3축 통합 → 복합 관광쇠퇴지수 (전체 시군구).
입력: analysis/data/index_axes.json (②매력·③연결), analysis/data/visits.json (①방문)
매칭: 시도명(약칭)+시군구명. 통합시는 방문 API의 '시 전체' 행과 정확 일치로 결합.
지수: 축별 = z합, 복합 = 3축 등가중 평균. z-표준화·지수는 '도지역 시·군(표본30+)' 모집단 기준.
출력: analysis/data/index_full.json
"""
import json
import pandas as pd

AXES = "analysis/data/index_axes.json"
VISITS = "analysis/data/visits.json"
OUT = "analysis/data/index_full.json"

DO_SIDO = {"경기","강원","충북","충남","전북","전남","경북","경남","제주"}  # 도지역(광역시·세종 제외)
SIDO_SHORT = {"서울특별시":"서울","부산광역시":"부산","대구광역시":"대구","인천광역시":"인천",
              "광주광역시":"광주","대전광역시":"대전","울산광역시":"울산","세종특별자치시":"세종",
              "경기도":"경기","강원도":"강원","강원특별자치도":"강원","충청북도":"충북","충청남도":"충남",
              "전라북도":"전북","전북특별자치도":"전북","전라남도":"전남","경상북도":"경북",
              "경상남도":"경남","제주특별자치도":"제주"}

def zscore(s):
    m, sd = s.mean(), s.std(ddof=0)
    return (s - m) / sd if sd else s * 0.0

def main():
    sv = pd.DataFrame(json.load(open(AXES, encoding="utf-8")))
    sv["sido_s"] = sv["sido"].map(lambda x: SIDO_SHORT.get(x, x))

    visits = json.load(open(VISITS, encoding="utf-8"))
    vmap = {}
    for v in visits.values():
        vmap[(v["sido"], v["name"])] = v      # (시도약칭, 시군구명) → 방문
    def look(row, y):
        v = vmap.get((row["sido_s"], row["sigungu"]))
        return v[f"y{y}"] if v else None
    for y in (2019, 2022, 2024):
        sv[f"v{y}"] = sv.apply(lambda r: look(r, y), axis=1)

    matched = sv["v2024"].notna().sum()
    print(f"방문 매칭: {matched}/{len(sv)} 시군구")
    unmatched = sv[(sv["sido_s"].isin(DO_SIDO)) & (sv["v2024"].isna())]["region"].tolist()
    print(f"도지역 미매칭({len(unmatched)}):", unmatched[:20])

    # 회복률(24/19)·최근추세(24/22)
    sv["recov"] = sv["v2024"] / sv["v2019"]
    sv["trend"] = sv["v2024"] / sv["v2022"]

    # 모집단: 도지역 시군 + 표본30+ + 3축 존재
    pop = (sv["sido_s"].isin(DO_SIDO) & (sv["n_attract"] >= 30)
           & sv["recov"].notna() & sv["trend"].notna()
           & sv["connect_centrality"].notna() & sv["revisit"].notna())
    P = sv[pop].copy()
    print(f"분석 모집단(도지역 시군, 표본30+): {len(P)}")

    # z-표준화 (모집단 기준)
    P["z_recov"] = -zscore(P["recov"])
    P["z_trend"] = -zscore(P["trend"])
    P["z_revisit"] = -zscore(P["revisit"])
    P["z_recommend"] = -zscore(P["recommend"])
    P["z_connect"] = -zscore(P["connect_centrality"])
    P["ax_visit"] = P["z_recov"] + P["z_trend"]
    P["ax_attract"] = P["z_revisit"] + P["z_recommend"]
    P["ax_connect"] = P["z_connect"]
    P["composite"] = (P["ax_visit"] + P["ax_attract"] + P["ax_connect"]) / 3

    # 병합해 저장 (모집단 밖은 composite=None)
    keep = ["region","sido","sido_s","sigungu","connect_centrality","revisit","recommend",
            "n_attract","v2019","v2022","v2024","recov","trend"]
    res = sv[keep].merge(
        P[["region","ax_visit","ax_attract","ax_connect","composite"]], on="region", how="left")
    res = res.sort_values("composite", ascending=False, na_position="last").reset_index(drop=True)
    res.to_json(OUT, orient="records", force_ascii=False, indent=1)
    print(f"저장: {OUT} ({len(res)} 시군구, 지수산출 {res['composite'].notna().sum()})")

    # 검증: 상위 15
    top = res[res["composite"].notna()].head(15)
    print("\n[복합 쇠퇴지수 상위 15]")
    for _, r in top.iterrows():
        print(f"  {r['composite']:+.2f}  {r['region']:14s} (방문{r['ax_visit']:+.1f}·매력{r['ax_attract']:+.1f}·연결{r['ax_connect']:+.1f})")

if __name__ == "__main__":
    main()
