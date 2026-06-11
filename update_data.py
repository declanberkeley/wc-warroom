"""Fetches Jeff's live leaderboard every run, rebuilds data.json.
Two parsing strategies: HTML table cells, then tag-stripped text regex."""
import json, re, datetime, html as H, urllib.request
from html.parser import HTMLParser
URL="https://www.jeffkeencharitychallenge.co.uk/worldcup2026/tables/Leaderboard.html"
OURS=["WCP-10964","WCP-10965","WCP-10966"]

class T(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.rows=[]; s.row=None; s.cell=None
    def _cc(s):
        if s.cell is not None and s.row is not None:
            s.row.append(" ".join(s.cell.split())); s.cell=None
    def _cr(s):
        s._cc()
        if s.row: s.rows.append(s.row)
        s.row=None
    def handle_starttag(s,tag,a):
        if tag=="tr": s._cr(); s.row=[]
        elif tag in("td","th"):
            if s.row is None: s.row=[]
            s._cc(); s.cell=""
    def handle_endtag(s,tag):
        if tag in("td","th"): s._cc()
        elif tag in("tr","table"): s._cr()
    def handle_data(s,d):
        if s.cell is not None: s.cell+=d

def fetch():
    req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (DecSamDashboard)","Cache-Control":"no-cache"})
    raw=urllib.request.urlopen(req,timeout=60).read()
    raw=raw.replace(b"\x00",b"")
    return raw.decode("utf-8","ignore"), len(raw)

def parse_cells(page):
    p=T(); p.feed(page); p.close(); p._cr(); out=[]
    for cells in p.rows:
        idx=[i for i,c in enumerate(cells) if c.startswith("WCP-")]
        if not idx: continue
        i=idx[0]
        ent=None; jok=""
        for k in range(len(cells)-1,i,-1):
            w=cells[k].split()
            if len(w)==8 and all(len(x)==3 and x.isupper() for x in w):
                ent=cells[k]; jok=cells[k-1]; break
        if not ent: continue
        try:
            out.append(dict(id=cells[i],name=cells[i+1],pts=int(cells[i+2]),
                            alive=int(cells[i+4]),joker=jok,entry=ent))
        except Exception: continue
    return out

def parse_text(page):
    txt=H.unescape(re.sub(r"<[^>]+>"," ",page))
    txt=re.sub(r"\s+"," ",txt)
    out=[]
    pat=re.compile(r"(WCP-\d{5}) (.+?) (-?\d+) \d+ (\d+) (?:-?\d+ ){7}([A-Za-z./ ]+?) ((?:[A-Z]{3} ){7}[A-Z]{3})")
    for m in pat.finditer(txt):
        out.append(dict(id=m.group(1),name=m.group(2).strip(),pts=int(m.group(3)),
                        alive=int(m.group(4)),joker=m.group(5).strip(),entry=m.group(6).strip()))
    return out

def main():
    base=json.load(open("data.json"))
    prev={e["id"]:e for e in base.get("leaderboard",[])}
    try:
        page,nb=fetch()
        a=parse_cells(page); b=parse_text(page)
        rows=a if len(a)>=len(b) else b
        print("fetched",nb,"bytes | cell-parser:",len(a),"rows | text-parser:",len(b),"rows | using",len(rows))
        if len(rows)<=500:
            print("tr tags seen:",page.lower().count("<tr"))
            print("sample:",page[:300].replace("\n"," "))
        if len(rows)>500:
            have={r["id"] for r in rows}
            for i in OURS:
                if i not in have and i in prev: rows.append(prev[i])
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
