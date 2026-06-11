"""Fetches Jeff's live leaderboard every run, rebuilds data.json. Static config below stays as-is."""
import json, re, datetime, urllib.request
URL="https://www.jeffkeencharitychallenge.co.uk/worldcup2026/tables/Leaderboard.html"
OURS=["WCP-10964","WCP-10965","WCP-10966"]
def fetch():
    req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (DecSamDashboard)","Cache-Control":"no-cache"})
    return urllib.request.urlopen(req,timeout=30).read().decode("utf-8","ignore")
def parse(html):
    # rows look like: ... WCP-10001 ... <numbers> ... Joker EntryCodes(8x3letters)
    txt=re.sub(r"<[^>]+>"," ",html)
    rows=[]
    pat=re.compile(r"(WCP-\d{5})\s+(.+?)\s+(\d+)\s+\d+\s+(\d+)\s+(?:\d+\s+){7}([A-Za-z./ ]+?)\s+((?:[A-Z]{3}\s+){7}[A-Z]{3})")
    for m in pat.finditer(txt):
        rows.append(dict(id=m.group(1),name=m.group(2).strip(),pts=int(m.group(3)),
                         alive=int(m.group(4)),joker=m.group(5).strip(),entry=m.group(6).strip()))
    return rows
def main():
    base=json.load(open("data.json"))
    try:
        rows=parse(fetch())
        if len(rows)>500:
            base["leaderboard"]=rows
            base["source"]="live from jeffkeencharitychallenge.co.uk"
        else:
            base["source"]="live parse too small (%d rows) - kept last good"%len(rows)
    except Exception as e:
        base["source"]="fetch failed: %s - kept last good"%e
    base["generated_at"]=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    base["total"]=len(base["leaderboard"])
    ranked=sorted(base["leaderboard"],key=lambda e:-e["pts"])
    pos={}; r=0; last=None
    for i,e in enumerate(ranked):
        if e["pts"]!=last: r=i+1; last=e["pts"]
        pos[e["id"]]=[r,e["pts"]]
    hist=base.setdefault("history",[])
    hist.append({"t":base["generated_at"],"r":{i:pos[i] for i in OURS if i in pos}})
    base["history"]=hist[-500:]
    json.dump(base,open("data.json","w"))
    print(base["source"],"|",len(base["leaderboard"]),"entries")
if __name__=="__main__": main()
