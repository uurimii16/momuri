# -*- coding: utf-8 -*-
"""
동선 네트워크 오버레이용 데이터 추출.
build_index.py와 똑같은 방식(국민여행조사 방문순서 → 방향 엣지, WT_DOM 가중)으로
'시도' 동선 네트워크를 만들어 지도 오버레이용 노드+엣지를 map/data/network.json에 저장한다.

필요: knts2025.sav  (build_index.py와 동일 위치 = 저장소 루트)
실행: python3 analysis/export_network.py
"""
import re, json, os
import pyreadstat, networkx as nx

SAV = "knts2025.sav"
OUT = "map/data/network.json"


def sido_of(name):        # "충청북도 진천군" -> "충청북도"
    return name.split()[0]


def main():
    _, meta = pyreadstat.read_sav(SAV, metadataonly=True)
    cols = meta.column_names
    spot_cols = [c for c in cols if re.fullmatch(r'D_TRA\d+_\d+_SPOT', c)]
    spot_map = {int(k): v for k, v in meta.variable_value_labels['D_TRA1_1_SPOT'].items()}
    df, _ = pyreadstat.read_sav(SAV, usecols=spot_cols + ['WT_DOM'])
    print(f"로드: {len(df):,}행 · SPOT컬럼 {len(spot_cols)}개")

    ks = sorted(set(int(re.match(r'D_TRA(\d+)_', c).group(1)) for c in spot_cols))
    vmax = max(int(re.match(r'D_TRA\d+_(\d+)_SPOT', c).group(1)) for c in spot_cols)

    # 방문순서 연속쌍(A->B, A!=B)을 WT_DOM 가중 합산 → 방향 엣지
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
                if x == x and int(x) in spot_map:
                    nd = sido_of(spot_map[int(x)])
                    if not seq or seq[-1] != nd:
                        seq.append(nd)
            for a, b in zip(seq, seq[1:]):
                if a != b:
                    edges[(a, b)] = edges.get((a, b), 0.0) + w

    G = nx.DiGraph()
    for (a, b), w in edges.items():
        G.add_edge(a, b, weight=w)

    deg = nx.degree_centrality(G)
    bet = nx.betweenness_centrality(G, weight='weight')

    nodes = [{"name": n, "degree": round(deg[n], 4), "betweenness": round(bet.get(n, 0.0), 4)}
             for n in G.nodes()]

    # 무방향 합산(A-B, B-A 합쳐 선 굵기용)
    und = {}
    for (a, b), w in edges.items():
        key = tuple(sorted((a, b)))
        und[key] = und.get(key, 0.0) + w
    edge_list = [{"source": a, "target": b, "weight": round(w, 1)} for (a, b), w in und.items()]
    edge_list.sort(key=lambda e: -e["weight"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"level": "sido", "nodes": nodes, "edges": edge_list}, f,
                  ensure_ascii=False, indent=1)

    print(f"\n저장: {OUT}  (노드 {len(nodes)}, 엣지 {len(edge_list)})")
    print("연결중심성 최상위:", [(n['name'], n['degree']) for n in sorted(nodes, key=lambda n: -n['degree'])[:3]])
    print("연결중심성 최하위:", [(n['name'], n['degree']) for n in sorted(nodes, key=lambda n: n['degree'])[:3]])
    print("가장 굵은 엣지 5:", [(e['source'], e['target'], e['weight']) for e in edge_list[:5]])


if __name__ == "__main__":
    main()
