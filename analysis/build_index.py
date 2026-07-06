# -*- coding: utf-8 -*-
"""
2025 국민여행조사 원자료(.SAV)로 복합 관광쇠퇴지수의 2개 축을 전체 시군구 단위로 복원한다.
  ② 매력 쇠퇴 = z(-재방문의향 A10) + z(-추천의향 A11)   [여행1차 첫 방문지 귀속]
  ③ 연결 소외 = z(-degree_centrality)                    [방문 순서 동선 네트워크]
방문 축(①)은 data.go.kr 방문자수 API(pull_locgo.py) 결과가 있으면 결합한다.
출력: analysis/data/index_axes.json  (시군구명 → 지표)
검증: 시도 레벨 연결중심성(제주 최하·충남 최상) 재현 확인.
"""
import re, json, math
import pyreadstat, pandas as pd, networkx as nx

SAV = "knts2025.sav"
OUT = "analysis/data/index_axes.json"

def zscore(s):
    m, sd = s.mean(), s.std(ddof=0)
    return (s - m) / sd if sd else s * 0.0

def sido_of(name):   # "경상남도 창녕군" -> "경상남도"
    return name.split()[0]

def full_of(name):   # 전체이름 그대로 (중구·동구 등 시도별 중복 방지)
    return name

def main():
    # --- 필요한 컬럼만 로드 ---
    _, meta = pyreadstat.read_sav(SAV, metadataonly=True)
    cols = meta.column_names
    spot_cols = [c for c in cols if re.fullmatch(r'D_TRA\d+_\d+_SPOT', c)]
    need = spot_cols + ['A10', 'A11', 'WT_DOM']
    spot_map = {int(k): v for k, v in meta.variable_value_labels['D_TRA1_1_SPOT'].items()}
    df, _ = pyreadstat.read_sav(SAV, usecols=need)
    print(f"로드: {len(df):,}행 · SPOT컬럼 {len(spot_cols)}개")

    # --- ③ 연결 소외: 방문 순서 → 방향 엣지 → degree_centrality ---
    # 여행차 k별로 v=1..17 순서의 SPOT 시퀀스를 만들어 연속쌍(A→B, A≠B)을 WT_DOM 가중 합산
    ks = sorted(set(int(re.match(r'D_TRA(\d+)_', c).group(1)) for c in spot_cols))
    vmax = max(int(re.match(r'D_TRA\d+_(\d+)_SPOT', c).group(1)) for c in spot_cols)

    def build_graph(node_key):
        """node_key: code->node 이름 함수 (시도 or 시군구)"""
        edges = {}
        for k in ks:
            seq_cols = [f'D_TRA{k}_{v}_SPOT' for v in range(1, vmax + 1) if f'D_TRA{k}_{v}_SPOT' in df.columns]
            sub = df[seq_cols + ['WT_DOM']].to_numpy()
            for row in sub:
                w = row[-1]
                if not (w == w) or w <= 0:
                    w = 1.0
                seq = []
                for x in row[:-1]:
                    if x == x and int(x) in spot_map:      # non-NaN & 유효코드
                        nd = node_key(spot_map[int(x)])
                        if not seq or seq[-1] != nd:        # 연속 중복 제거
                            seq.append(nd)
                for a, b in zip(seq, seq[1:]):
                    if a != b:
                        edges[(a, b)] = edges.get((a, b), 0.0) + w
        G = nx.DiGraph()
        for (a, b), w in edges.items():
            G.add_edge(a, b, weight=w)
        return G

    # 시도 검증
    Gs = build_graph(sido_of)
    dcs = nx.degree_centrality(Gs)
    ranked = sorted(dcs.items(), key=lambda x: x[1])
    print(f"\n[검증] 시도 연결중심성 (노드 {Gs.number_of_nodes()}, 엣지 {Gs.number_of_edges()})")
    print("  최하위:", [(n, round(v, 3)) for n, v in ranked[:3]])
    print("  최상위:", [(n, round(v, 3)) for n, v in ranked[-3:]])

    # 시군구 본계산 (전체이름 키)
    Gg = build_graph(full_of)
    dcg = nx.degree_centrality(Gg)
    print(f"\n[시군구] 노드 {Gg.number_of_nodes()}, 엣지 {Gg.number_of_edges()}")

    # --- ② 매력 쇠퇴: A10/A11를 여행1차 첫 방문지(D_TRA1_1_SPOT)에 귀속, WT_DOM 가중평균 ---
    a = df[['D_TRA1_1_SPOT', 'A10', 'A11', 'WT_DOM']].copy()
    a = a[a['D_TRA1_1_SPOT'].apply(lambda x: x == x and int(x) in spot_map)]
    a['region'] = a['D_TRA1_1_SPOT'].apply(lambda x: spot_map[int(x)])
    a['w'] = a['WT_DOM'].where(a['WT_DOM'] > 0, 1.0)

    def wmean(g, col):
        w = g['w']; v = g[col]
        m = v.notna()
        return (v[m] * w[m]).sum() / w[m].sum() if w[m].sum() else float('nan')

    rows = []
    for name, g in a.groupby('region'):
        rows.append({
            'region': name,
            'n_attract': int(g['A10'].notna().sum()),
            'revisit': wmean(g, 'A10'),
            'recommend': wmean(g, 'A11'),
        })
    attract = {r['region']: r for r in rows}

    # --- 통합 테이블 (전체이름 기준) ---
    all_names = set(dcg) | set(attract)
    recs = []
    for nm in all_names:
        r = attract.get(nm, {})
        recs.append({
            'region': nm,
            'sido': sido_of(nm),
            'sigungu': nm.split()[-1],
            'connect_centrality': dcg.get(nm),
            'revisit': r.get('revisit'),
            'recommend': r.get('recommend'),
            'n_attract': r.get('n_attract', 0),
        })
    out = pd.DataFrame(recs)

    # z-표준화 (표본 30건↑만 매력 z 계산)
    valid = out['n_attract'] >= 30
    out['z_connect_isol'] = -zscore(out['connect_centrality'].fillna(out['connect_centrality'].mean()))
    zr = -zscore(out.loc[valid, 'revisit'])
    zc = -zscore(out.loc[valid, 'recommend'])
    out['z_attract_decl'] = None
    out.loc[valid, 'z_attract_decl'] = (zr + zc).values

    out = out.sort_values('region').reset_index(drop=True)
    out.to_json(OUT, orient='records', force_ascii=False, indent=1)
    print(f"\n저장: {OUT}  ({len(out)} 시군구)")
    print("매력 z 계산 대상(표본30+):", int(valid.sum()))
    # 참고: 재방문의향 최고/최저 (README 검증: 최고 강진·영암·고흥·장흥 / 최저 진천·괴산)
    v = out.loc[valid].sort_values('revisit')
    print("재방문의향 최저5:", list(v['region'].head(5)))
    print("재방문의향 최고5:", list(v['region'].tail(5)))

if __name__ == "__main__":
    main()
