import json, os, re, glob, html as htmlmod, hashlib
from urllib.parse import quote, unquote

OUT="site"
pages=json.load(open("pages_wikitext.json",encoding="utf-8"))

# ---- naming: disk name is human-readable (/ -> __), href is percent-encoded once ----
def diskname(t):
    n=t.replace("/","__")
    n=re.sub(r'[:?*"<>|]',"-",n); n=re.sub(r'([ .]+)$',lambda m:"_"*len(m.group(1)),n)
    if len(n.encode("utf-8"))>200:   # safety for over-long titles
        n=n[:60]+"~"+hashlib.md5(t.encode()).hexdigest()[:10]
    return n
def href(t): return quote(diskname(t)+".html")

# ---- classify redirects vs content ----
redirects={}; content_titles=[]
for t,e in pages.items():
    wt=(e["wikitext"] or "").strip()
    m=re.match(r'#redirect\s*\[\[([^\]|#]+)',wt,re.I)
    if m: redirects[t]=m.group(1).strip().replace("_"," ")
    else: content_titles.append(t)
title_set=set(content_titles)|set(redirects)

# collision check
seen={}
for t in list(content_titles)+list(redirects):
    d=diskname(t)
    if d in seen: print("COLLISION:",repr(t),"vs",repr(seen[d]))
    seen[d]=t

rendered={}
for p in glob.glob("html/*.json"):
    d=json.load(open(p,encoding="utf-8")); rendered[d["title"]]=d
def get_html(t):
    return rendered.get(t)

def resolve_link(h):
    frag=""
    if "#" in h: h,frag=h.split("#",1)
    tgt=unquote(h[len("/wiki/"):]).replace("_"," ")
    seen=set()
    while tgt in redirects and tgt not in seen:
        seen.add(tgt); tgt=redirects[tgt]
    if tgt in title_set or get_html(tgt):
        return "./"+href(tgt)+("#"+frag if frag else "")
    return "https://breakmycase.fandom.com/wiki/"+quote(h[len('/wiki/'):])+("#"+frag if frag else "")

def fix_lazy(h):
    def repl(m):
        tag=m.group(0)
        ds=re.search(r'data-src="([^"]+)"',tag)
        if ds: tag=re.sub(r'src="data:[^"]*"','src="%s"'%ds.group(1).replace("\\","\\\\"),tag)
        dss=re.search(r'data-srcset="([^"]+)"',tag)
        if dss and 'srcset=' in tag:
            tag=re.sub(r'srcset="[^"]*"','srcset="%s"'%dss.group(1).replace("\\","\\\\"),tag)
        return tag
    return re.sub(r'<img[^>]+>',repl,h)
def clean(h):
    h=fix_lazy(h)
    h=re.sub(r'href="(/wiki/[^"]+)"',lambda m:'href="%s"'%resolve_link(m.group(1)),h)
    h=re.sub(r'<span class="mw-editsection">.*?</span>','',h,flags=re.S)
    return h

SHELL='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Break My Case Archive</title>
<link rel="stylesheet" href="../assets/style.css"></head>
<body><div class="topbar"><a href="../index.html">← Archive Index</a>
<span class="src">source: <a href="{live}" target="_blank" rel="noopener">breakmycase.fandom.com</a></span></div>
<main class="wiki"><h1 class="page-title">{title}</h1>{body}</main>
<footer>Archived from Break My Case Wiki (Fandom). Text CC BY-SA; images © respective owners, loaded from Fandom CDN. Personal archive.</footer>
</body></html>'''

built=0; fallback=[]
for t in content_titles:
    d=get_html(t)
    if d: body=clean(d["html"])
    else:
        fallback.append(t)
        body='<div class="fallback-note">Rendered HTML unavailable (page too large to render via API); showing raw wiki source.</div><pre class="wikitext">%s</pre>'%htmlmod.escape(pages[t]["wikitext"] or "")
    live="https://breakmycase.fandom.com/wiki/"+quote(t.replace(" ","_"))
    open(OUT+"/articles/"+diskname(t)+".html","w",encoding="utf-8").write(
        SHELL.format(title=htmlmod.escape(t),body=body,live=live))
    built+=1

for t,tgt in redirects.items():
    tt=tgt; s=set()
    while tt in redirects and tt not in s: s.add(tt); tt=redirects[tt]
    if tt in title_set or get_html(tt):
        open(OUT+"/articles/"+diskname(t)+".html","w",encoding="utf-8").write(
          '<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=./%s"><a href="./%s">→ %s</a>'%(href(tt),href(tt),htmlmod.escape(tt)))

# index data: store DISK name (decoded) in "f"
index=[{"t":t,"f":diskname(t)+".html","c":(get_html(t)["categories"] if get_html(t) else [])} for t in content_titles]
json.dump(index,open(OUT+"/data/pages.json","w",encoding="utf-8"),ensure_ascii=False)
print("articles:",built,"| redirects:",len(redirects),"| fallback:",fallback)
