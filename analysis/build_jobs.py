# -*- coding: utf-8 -*-
"""
로컬 일자리(공공기관 채용) 수집 → map/data/jobs.json  (과제4 체류·생활인구 레이어)
- 출처: 기획재정부_공공기관 채용정보(잡알리오). data.go.kr 1051000/recruitment/list.
  개인 data.go.kr 공용 인증키로 작동(워크넷 채용정보 API는 기업회원 전용이라 대체).
- 잡알리오 근무지역은 '시도' 단위 → momuri 지역(시군구)을 시도코드로 조회하고,
  시군구명 텍스트매칭으로 '진짜 로컬' 채용을 우선 노출(local), 나머지는 시도 단위(sido).
- 진행 중(접수마감 오늘 이후)·비전국(근무지역 소수) 공고만.
실행: TOURAPI_KEY=<data.go.kr키> python analysis/build_jobs.py   (JOBALIO_KEY/DATAGO_KEY도 인식)
"""
import os, sys, json, datetime, urllib.request, urllib.parse

KEY = (os.environ.get("JOBALIO_KEY") or os.environ.get("TOURAPI_KEY")
       or os.environ.get("DATAGO_KEY") or "").strip()
SRC = "map/data/momuri.json"
OUT = "map/data/jobs.json"
BASE = "https://apis.data.go.kr/1051000/recruitment/list"
TODAY = datetime.date.today().strftime("%Y%m%d")

# 잡알리오 근무지역 코드(시도). momuri sido 약칭 기준.
RGN = {"서울":"R3010","인천":"R3011","대전":"R3012","대구":"R3013","부산":"R3014",
       "광주":"R3015","울산":"R3016","경기":"R3017","강원":"R3018","충남":"R3019",
       "충북":"R3020","경북":"R3021","경남":"R3022","전남":"R3023","전북":"R3024",
       "제주":"R3025","세종":"R3026"}

def alio(rgncode, page=1, rows=100):
    q = urllib.parse.urlencode({"serviceKey": KEY, "pageNo": page, "numOfRows": rows,
                                "resultType": "json", "workRgnLst": rgncode})
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=60) as r:
        return json.load(r)

def fetch_sido(rgncode, want=120, max_pages=4):
    """해당 시도의 '진행 중·비전국' 공고 수집(전국 공고 제외)."""
    got = []
    for page in range(1, max_pages + 1):
        d = alio(rgncode, page=page)
        rows = d.get("result", []) or []
        if not rows:
            break
        for x in rows:
            end = x.get("pbancEndYmd") or ""
            rgns = [r for r in (x.get("workRgnLst") or "").split(",") if r]
            if end and end < TODAY:      # 마감 지난 공고 제외
                continue
            if len(rgns) >= 8:           # 사실상 전국 공고 제외(로컬성 낮음)
                continue
            got.append(x)
        if len(got) >= want:
            break
    return got

def slim(x):
    return {"inst": x.get("instNm"), "title": x.get("recrutPbancTtl"),
            "ncs": x.get("ncsCdNmLst"), "hire": x.get("hireTypeNmLst"),
            "rgn": x.get("workRgnNmLst"), "recruitSe": x.get("recrutSeNm"),
            "nope": x.get("recrutNope"), "bgn": x.get("pbancBgngYmd"),
            "end": x.get("pbancEndYmd"), "url": x.get("srcUrl")}

def deeplink(rgncode):
    # 잡알리오 채용검색(시도) — 실물 최신 목록으로 이동
    return f"https://job.alio.go.kr/recruit.do?pageNo=1&workRegionArr={rgncode}"

def main():
    if not KEY:
        print("data.go.kr 인증키 없음(env TOURAPI_KEY/JOBALIO_KEY)"); sys.exit(1)
    regions = json.load(open(SRC, encoding="utf-8"))
    # 시도별 1회만 조회(같은 시도의 여러 시군구가 공유)
    sido_cache = {}
    result = {}
    for r in regions:
        sido = r["sido"]; sig = r["sigungu"]
        code = RGN.get(sido)
        if not code:
            print("  스킵(시도코드 없음):", sido, sig); continue
        if code not in sido_cache:
            sido_cache[code] = fetch_sido(code)
        pool = sido_cache[code]
        # 시군구명(예: '상주시'→'상주') 텍스트매칭 = 진짜 로컬
        stem = sig[:-1] if sig[-1] in "시군구" else sig
        def hit(x):
            blob = f"{x.get('instNm','')} {x.get('recrutPbancTtl','')} {x.get('aplyQlfcCn','')}"
            return stem in blob
        local = [slim(x) for x in pool if hit(x)]
        local.sort(key=lambda j: j.get("end") or "99999999")
        sido_jobs = [slim(x) for x in pool if not hit(x)]
        sido_jobs.sort(key=lambda j: j.get("end") or "99999999")
        result[sig] = {"sido": sido, "rgncode": code, "deeplink": deeplink(code),
                       "local": local[:6], "sido_jobs": sido_jobs[:6],
                       "sido_total": len(pool)}
        print(f"  {r['region']:16s} 로컬 {len(local)} · 시도풀 {len(pool)}")
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT} ({len(result)}개 지역)")

if __name__ == "__main__":
    main()
