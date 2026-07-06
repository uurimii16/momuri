import urllib.request, json, time, pickle, sys
from collections import defaultdict
KEY="YOUR_DATA_GO_KR_SERVICE_KEY"
B="https://apis.data.go.kr/B551011/DataLabService/locgoRegnVisitrDDList"
OUT="/private/tmp/claude-501/-Users-yurimii/039b1be0-5157-4f64-b845-7870afc85762/scratchpad/"

def pull_year(y, touset={"2"}):
    tot=defaultdict(float); nm={}; page=1; got=0; total=None
    while True:
        url=(f"{B}?serviceKey={KEY}&numOfRows=9000&pageNo={page}&MobileOS=ETC&MobileApp=t"
             f"&startYmd={y}0101&endYmd={y}1231&_type=json")
        for att in range(5):
            try: r=json.load(urllib.request.urlopen(url,timeout=120)); break
            except Exception as e:
                if att==4: raise
                time.sleep(3)
        body=r["response"]["body"]; total=int(body["totalCount"])
        items=body["items"]; it=items["item"] if items else []
        if isinstance(it,dict): it=[it]
        for i in it:
            if i["touDivCd"] in touset:
                tot[i["signguCode"]]+=float(i["touNum"]); nm[i["signguCode"]]=i["signguNm"]
        got+=len(it)
        if got>=total or not it: break
        page+=1
    return tot,nm,total,got

data={}; names={}; log=open(OUT+"pull_progress.txt","w")
for y in [2019,2022,2024]:
    t=time.time(); tot,nm,total,got=pull_year(y); data[y]=tot; names.update(nm)
    log.write(f"{y}: {got}/{total} records, 시군구 {len(tot)}, 외지인합 {sum(tot.values())/1e8:.1f}억 ({time.time()-t:.0f}s)\n"); log.flush()
pickle.dump({"data":data,"names":names}, open(OUT+"locgo_visitors.pkl","wb"))
log.write("DONE\n"); log.close()
