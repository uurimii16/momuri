# -*- coding: utf-8 -*-
"""
[Phase 1] 전국 '숨은 매력지' 후보 테이블 생성.
입력: index_full.json(복합쇠퇴지수·3축), heritage_density.pkl(시군구 문화유산 수)
알고리즘:
  1) z-표준화: 서로 다른 척도를 (x-평균)/표준편차 로 통일
  2) 문화유산은 편포(왜도) 심해 log1p 후 z (소수 지역 몰림 완화)
  3) 숨은매력지 점수 = z(쇠퇴) + z(문화유산자산)  [등가중]
  4) 사분면 세그: 쇠퇴>중위 & 자산>중위 = '숨은 매력지(문화유산형)'
출력: analysis/data/candidates.json
"""
import json
import numpy as np
import pandas as pd

def z(s):
    return (s - s.mean()) / s.std(ddof=0)

def main():
    idx = pd.DataFrame(json.load(open("analysis/data/index_full.json", encoding="utf-8")))
    h = pd.read_pickle("analysis/data/heritage_density.pkl")   # {(시도약칭, 시군구): 문화유산수}

    P = idx[idx["composite"].notna()].copy()                   # 지수 산출된 도지역 시군
    P["heritage"] = P.apply(lambda r: int(h.get((r["sido_s"], r["sigungu"]), 0)), axis=1)

    # --- 표준화 ---
    P["z_decline"] = z(P["composite"])                         # 쇠퇴 (높을수록 쇠퇴)
    P["z_asset"] = z(np.log1p(P["heritage"]))                  # 문화유산 자산 (log 후 z)
    P["hidden_score"] = P["z_decline"] + P["z_asset"]          # 숨은매력지 점수

    # --- 사분면 세그멘테이션 ---
    med_d = P["composite"].median()
    med_h = P["heritage"].median()
    def seg(r):
        hi_d, hi_h = r["composite"] >= med_d, r["heritage"] >= med_h
        if hi_d and hi_h:      return "숨은매력지(문화유산형)"
        if hi_d and not hi_h:  return "자연힐링형(자산희소)"
        if not hi_d and hi_h:  return "자산풍부·쇠퇴낮음"
        return "기타"
    P["segment"] = P.apply(seg, axis=1)
    P["theme"] = P["heritage"].apply(lambda c: "문화유산형" if c >= med_h else "자연힐링형")

    cols = ["region","sido_s","sigungu","composite","ax_visit","ax_attract","ax_connect",
            "heritage","z_decline","z_asset","hidden_score","segment","theme"]
    out = P[cols].sort_values("hidden_score", ascending=False).reset_index(drop=True)
    out.to_json("analysis/data/candidates.json", orient="records", force_ascii=False, indent=1)
    print(f"저장: analysis/data/candidates.json ({len(out)} 시군)")
    print(f"중위선  쇠퇴={med_d:.2f}  문화유산={med_h:.0f}건")
    print(f"세그 분포: {out['segment'].value_counts().to_dict()}")

    hs = out[out["segment"] == "숨은매력지(문화유산형)"].head(12)
    print("\n[숨은매력지(문화유산형) 상위 12]")
    for _, r in hs.iterrows():
        print(f"  점수{r['hidden_score']:+.2f}  {r['region']:14s} 쇠퇴{r['composite']:+.2f}·유산{r['heritage']:>4d}건 "
              f"(방문{r['ax_visit']:+.1f}·매력{r['ax_attract']:+.1f}·연결{r['ax_connect']:+.1f})")

if __name__ == "__main__":
    main()
