# -*- coding: utf-8 -*-
"""
① 방문 축: 한국관광공사 지역별 방문자수 API(data.go.kr 15101972)로
   시군구별 '외지인(touDivCd=2)' 연간 방문자수를 2019·2022·2024 수집·합산한다.
- 서비스키는 환경변수 DATAGO_KEY로 전달(코드/커밋에 저장 금지).
- 출력: analysis/data/visits.json  (집계값만; 원자료 아님)
실행: DATAGO_KEY=... python analysis/pull_visits.py
"""
import os, sys, json, time, urllib.request
from collections import defaultdict

KEY = os.environ.get("DATAGO_KEY", "").strip()
B = "https://apis.data.go.kr/B551011/DataLabService/locgoRegnVisitrDDList"
YEARS = [2019, 2022, 2024]
OUT = "analysis/data/visits.json"

# 행정표준 시도코드(앞 2자리) → 시도 약칭
SIDO = {"11":"서울","26":"부산","27":"대구","28":"인천","29":"광주","30":"대전",
        "31":"울산","36":"세종","41":"경기","42":"강원","51":"강원","43":"충북",
        "44":"충남","45":"전북","52":"전북","46":"전남","47":"경북","48":"경남","50":"제주"}

def pull_year(y):
    tot = defaultdict(float); nm = {}; page = 1; got = 0; total = None
    while True:
        url = (f"{B}?serviceKey={KEY}&numOfRows=9000&pageNo={page}&MobileOS=ETC&MobileApp=tourgo"
               f"&startYmd={y}0101&endYmd={y}1231&_type=json")
        for att in range(5):
            try:
                r = json.load(urllib.request.urlopen(url, timeout=180)); break
            except Exception:
                if att == 4: raise
                time.sleep(3)
        body = r["response"]["body"]; total = int(body["totalCount"])
        items = body.get("items") or {}
        it = items.get("item", []) if isinstance(items, dict) else []
        if isinstance(it, dict): it = [it]
        for i in it:
            if i.get("touDivCd") == "2":               # 외지인만
                code = i["signguCode"]
                tot[code] += float(i["touNum"]); nm[code] = i["signguNm"]
        got += len(it)
        if got >= total or not it: break
        page += 1
    return tot, nm, total, got

def main():
    if not KEY:
        print("환경변수 DATAGO_KEY 없음"); sys.exit(1)
    data = {}; names = {}
    for y in YEARS:
        t = time.time(); tot, nm, total, got = pull_year(y)
        data[y] = tot; names.update(nm)
        print(f"{y}: {got:,}/{total:,} rec · 시군구 {len(tot)} · 외지인합 {sum(tot.values())/1e8:.1f}억 ({time.time()-t:.0f}s)")

    # 집계 저장: code -> {name, sido, y2019, y2022, y2024}
    codes = set().union(*[set(data[y]) for y in YEARS])
    out = {}
    for c in sorted(codes):
        out[c] = {
            "name": names.get(c, ""),
            "sido": SIDO.get(c[:2], c[:2]),
            **{f"y{y}": round(data[y].get(c, 0.0), 1) for y in YEARS},
        }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: {OUT} ({len(out)} 시군구코드)")

if __name__ == "__main__":
    main()
