#!/usr/bin/env python3
"""
Rebuild the Break My Case Wiki archive from the live wiki.
Usage:  python3 refresh_archive.py
Steps: enumerate pages -> fetch wikitext -> fetch rendered HTML -> fetch media list -> build site.
Requires: Python 3.8+ (stdlib only). Run from the repo root; writes into ./ (index.html, articles/, data/).
Politeness: light rate-limiting + small thread pool. This hits the public MediaWiki API only.
"""
import urllib.request, urllib.parse, json, time, os, re, html as htmlmod, hashlib, glob
from concurrent.futures import ThreadPoolExecutor

API="https://breakmycase.fandom.com/api.php"
H={"User-Agent":"Mozilla/5.0 (personal-archival; MediaWiki API)"}
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)  # repo root (scripts/ lives under it)
WORK=os.path.join(HERE,"_work"); os.makedirs(WORK,exist_ok=True)
os.makedirs(os.path.join(ROOT,"articles"),exist_ok=True)
os.makedirs(os.path.join(ROOT,"data"),exist_ok=True)

def api(params, post=False):
    params["format"]="json"
    if post:
        req=urllib.request.Request(API,data=urllib.parse.urlencode(params,doseq=True).encode(),headers=H)
    else:
        req=urllib.request.Request(API+"?"+urllib.parse.urlencode(params,doseq=True),headers=H)
    for a in range(4):
        try:
            with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
        except Exception: time.sleep(1.2*(a+1))
    return None

def enumerate_pages():
    out=[]; cont={}
    while True:
        p={"action":"query","list":"allpages","apnamespace":0,"aplimit":"500"}; p.update(cont)
        d=api(p)
        out+=[x["title"] for x in d["query"]["allpages"]]
        if "continue" in d: cont=d["continue"]; time.sleep(0.15)
        else: break
    return out

def fetch_wikitext(titles):
    pages={}
    for i in range(0,len(titles),50):
        d=api({"action":"query","prop":"revisions|images","rvprop":"content","rvslots":"main",
               "imlimit":"500","titles":"|".join(titles[i:i+50])},post=True)
        for _,pg in d.get("query",{}).get("pages",{}).items():
            e=pages.setdefault(pg["title"],{"wikitext":None,"images":[]})
            revs=pg.get("revisions")
            if revs: e["wikitext"]=revs[0].get("slots",{}).get("main",{}).get("*")
            e["images"]=[im["title"] for im in pg.get("images",[])]
        time.sleep(0.15)
    return pages

def dname(t):
    n=t.replace("/","__")
    return n if len(n.encode())<=200 else n[:60]+"~"+hashlib.md5(t.encode()).hexdigest()[:10]

def fetch_html(titles):
    def work(t):
        fn=os.path.join(WORK,"html_"+dname(t)+".json")
        if os.path.exists(fn): return
        d=api({"action":"parse","page":t,"prop":"text|categories","redirects":1})
        if d and "parse" in d:
            pr=d["parse"]
            json.dump({"title":pr.get("title"),"html":pr.get("text",{}).get("*",""),
                       "categories":[c.get("*") for c in pr.get("categories",[])]},
                      open(fn,"w",encoding="utf-8"),ensure_ascii=False)
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(work,titles))

def fetch_images():
    images={}; cont={}
    while True:
        p={"action":"query","list":"allimages","ailimit":"500","aiprop":"url|size|mime"}; p.update(cont)
        d=api(p)
        for im in d["query"]["allimages"]:
            images[im["title"]]={"url":im.get("url"),"w":im.get("width"),"h":im.get("height"),
                                 "mime":im.get("mime"),"size":im.get("size")}
        if "continue" in d: cont=d["continue"]; time.sleep(0.15)
        else: break
    return images

# (build step is identical to build_site.py in this repo; see that file)
if __name__=="__main__":
    print("1/4 enumerating pages…"); titles=enumerate_pages(); print("  ",len(titles),"pages")
    print("2/4 wikitext…"); pages=fetch_wikitext(titles)
    json.dump(pages,open(os.path.join(WORK,"pages_wikitext.json"),"w",encoding="utf-8"),ensure_ascii=False)
    print("3/4 rendered html (this is the slow part)…"); fetch_html(
        [t for t,e in pages.items() if e["wikitext"] and not (e["wikitext"] or "").strip().lower().startswith("#redirect")])
    print("4/4 media list…"); img=fetch_images()
    json.dump(img,open(os.path.join(ROOT,"data","all_images.json"),"w",encoding="utf-8"),ensure_ascii=False)
    print("Done fetching. Now run build_site.py to (re)generate articles/ and data/pages.json.")
