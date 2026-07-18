#!/usr/bin/env python3
"""Parse event/banner data from the wiki into data/events.json (powers index.html + event.html).
Reads scripts/_work/pages_wikitext.json + data/all_images.json + rendered HTML in scripts/_work/html_*.
Run after refresh_archive.py. Stdlib only."""
import json,re,hashlib,glob,os
from urllib.parse import quote
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); WORK=os.path.join(HERE,"_work")
pages=json.load(open(os.path.join(WORK,"pages_wikitext.json"),encoding="utf-8"))
images=json.load(open(os.path.join(ROOT,"data","all_images.json"),encoding="utf-8"))
imgset={k[5:]:v for k,v in images.items()}
H={}
for p in glob.glob(os.path.join(WORK,"html_*.json")):
    d=json.load(open(p,encoding="utf-8")); H[d["title"]]=d["html"]
def diskname(t):
    n=t.replace("/","__"); n=re.sub(r'[:?*"<>|]',"-",n); n=re.sub(r'([ .]+)$',lambda m:"_"*len(m.group(1)),n); return n if len(n.encode())<=200 else n[:60]+"~"+hashlib.md5(t.encode()).hexdigest()[:10]
def art_href(t): return "articles/"+quote(diskname(t)+".html")
def img_url(fn): v=imgset.get(fn); return v["url"] if v else None
def cards_from_html(t):
    out=[]
    for page in [t,t+"/Gacha",t+"/Event Story",t+"/Cards"]:
        h=H.get(page,"")
        for u in re.findall(r'(?:data-src|src)="(https://static\.wikia[^"]+)"',h):
            if "Card_illust" in u: out.append(re.sub(r'/revision/latest/[^?]*\?','/revision/latest?',u))
    seen=set(); ded=[]
    for u in out:
        k=(re.search(r'/([^/]+)/revision',u) or [None,u])[1]
        if k not in seen: seen.add(k); ded.append(u)
    return ded
chars_by_token={}
for t,e in pages.items():
    if "/" in t: continue
    if re.search(r'\{\{Character',e["wikitext"] or ""):
        for tok in t.split(): chars_by_token.setdefault(tok.lower(),t)
samples={}
for fn in imgset:
    m=re.match(r'Sample-([a-z]+)-\d+\.ogg$',fn,re.I)
    if m: samples.setdefault(m.group(1).lower(),[]).append(fn)
def resolve_char(code):
    if not code: return None
    page=chars_by_token.get(code.strip().lower())
    if not page: return None
    vs=[img_url(f) for tok in page.split() for f in sorted(samples.get(tok.lower(),[]))]
    return {"code":code.strip().lower(),"name":page,"href":art_href(page),"voices":[v for v in vs if v][:3]}
def fields(wt):
    d={}
    for m in re.finditer(r'\|\s*([\w-]+)\s*=\s*([^\n|]*)',wt): d.setdefault(m.group(1).strip(),m.group(2).strip())
    return d
def pdate(s):
    if not s: return None,None
    m=re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',s)
    if not m: return None,s
    y,mo,da=m.groups(); return f"{int(y):04d}-{int(mo):02d}-{int(da):02d}",f"{int(y)}.{int(mo):02d}.{int(da):02d}"
events=[]
for t,e in pages.items():
    wt=e["wikitext"] or ""
    if not re.search(r'\{\{Event Articles',wt): continue
    f=fields(wt); kind=(re.search(r'\{\{Event Articles/(\w+)',wt) or [None,None])[1]
    siso,sdisp=pdate(f.get("event-start")); eiso,edisp=pdate(f.get("event-end"))
    name=re.sub(r'^(Prequel|Travelogue|Cafe|Event)\s*[:\-]\s*','',re.sub(r'^\([^)]*\)\s*','',t)).strip()
    codes=[]
    for key in ["SSR1-chara","SSR2-chara","SSR3-chara","SR1-chara","R1-chara","event-chara"]:
        c=f.get(key)
        if c and c not in codes: codes.append(c)
    subs={s:art_href(t+"/"+s) for s in ["Event Story","Gacha","Gacha Event","Cards"] if t+"/"+s in pages}
    events.append({"id":int(re.sub(r'\D','',f.get("event-id","0")) or 0),"kind":kind,"title":t,"name":name,
        "kanji":f.get("event-kanji"),"start":siso,"start_disp":sdisp,"end":eiso,"end_disp":edisp,
        "dept":f.get("dept"),"attribute":f.get("event-attribute"),"banner":img_url(f.get("event-image","")),
        "song":f.get("event-song"),"song_artist":f.get("event-song-artist"),
        "chars":[c for c in (resolve_char(x) for x in codes) if c],"cards":cards_from_html(t),
        "article":art_href(t),"subs":subs})
events.sort(key=lambda x:(x["start"] or "9999",x["id"]))
json.dump(events,open(os.path.join(ROOT,"data","events.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("wrote data/events.json:",len(events),"events")
