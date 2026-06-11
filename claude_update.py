"""OPTIONAL daily job: asks Claude (with web search) to update Venn condition
statuses, refresh prize-odds estimates, and fetch today's full match slate.
Needs ANTHROPIC_API_KEY env var (GitHub secret). Exits quietly without one."""
import json, os, datetime, urllib.request
KEY=os.environ.get("ANTHROPIC_API_KEY","").strip()
if not KEY:
    print("no ANTHROPIC_API_KEY - skipping odds refresh"); raise SystemExit(0)
base=json.load(open("data.json"))
today=datetime.date.today().isoformat()
payload={
 "model":"claude-sonnet-4-6","max_tokens":3000,
 "tools":[{"type":"web_search_20250305","name":"web_search"}],
 "messages":[{"role":"user","content":(
  "You maintain a World Cup 2026 fantasy dashboard. Today is "+today+
  ". Search the web for the latest 2026 World Cup results, eliminations and today's schedule, then provide:\n"
  "1) condition statuses (pending|on|banked|dead) based ONLY on what has actually happened;\n"
  "2) p_top5 prize-odds estimates (%) for the three tickets, nudged sensibly from results so far;\n"
  "3) today: ALL World Cup matches kicking off TODAY ("+today+") - the full slate for the whole "
  "tournament, every game not just these tickets - with UK kick-off times (24h HH:MM) and stage.\n"
  "Current conditions: "+json.dumps(base.get("conditions",[]))+"\n"
  "Current ticket models: "+json.dumps({k:v["model"] for k,v in base["ticket_meta"].items()})+"\n"
  "Tickets: T1=WCP-10964 (joker France: FRA SPA MOR COL AUT CAN DRC SAU), "
  "T2=WCP-10965 (joker Spain: SPA ENG MOR COL AUT CAN PAN DRC), "
  "T3=WCP-10966 (joker France: FRA ARG JAP URU AUT IVO UZB CVD).\n"
  "Reply with ONLY JSON, no markdown: {\"conditions\":[{\"id\":...,\"status\":...}],"
  "\"odds\":{\"WCP-10964\":1.0,\"WCP-10965\":1.0,\"WCP-10966\":1.0},"
  "\"today\":[{\"ko\":\"17:00\",\"match\":\"Spain v Cape Verde\",\"stage\":\"Group H\"}],"
  "\"note\":\"one line\"}")}]}
req=urllib.request.Request("https://api.anthropic.com/v1/messages",
 data=json.dumps(payload).encode(),
 headers={"content-type":"application/json","x-api-key":KEY,"anthropic-version":"2023-06-01"})
try:
    out=json.load(urllib.request.urlopen(req,timeout=180))
    txt="".join(b.get("text","") for b in out.get("content",[]) if b.get("type")=="text")
    txt=txt[txt.find("{"):txt.rfind("}")+1]
    upd=json.loads(txt)
    smap={c["id"]:c["status"] for c in upd.get("conditions",[]) if c.get("status") in ("pending","on","banked","dead")}
    for c in base.get("conditions",[]):
        if c["id"] in smap: c["status"]=smap[c["id"]]
    for k,v in (upd.get("odds") or {}).items():
        if k in base["ticket_meta"] and isinstance(v,(int,float)) and 0<=v<=100:
            base["ticket_meta"][k]["model"]["p_top5"]=round(float(v),2)
    tdy=upd.get("today")
    if isinstance(tdy,list):
        clean=[]
        for m in tdy[:24]:
            if isinstance(m,dict) and m.get("match"):
                clean.append({"ko":str(m.get("ko","TBC"))[:5],
                              "match":str(m["match"])[:60],
                              "stage":str(m.get("stage",""))[:24]})
        base["today_matches"]={"date":today,"list":clean}
    base["odds_updated"]=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    base["odds_note"]=str(upd.get("note",""))[:200]
    json.dump(base,open("data.json","w"))
    print("refreshed:",base["odds_note"],"|",len(base.get("today_matches",{}).get("list",[])),"matches today")
except Exception as e:
    print("claude update failed, data untouched:",e)
