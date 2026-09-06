import csv, json, collections, os, io, zipfile, urllib.request, sys
HERE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(HERE,".cache"); os.makedirs(CACHE,exist_ok=True)
os.chdir(CACHE)
OUT=HERE
from datetime import datetime
from zoneinfo import ZoneInfo
JAN=datetime(2026,1,15,12); JUL=datetime(2026,7,15,12)
_sig={}
def sig(tz):
    if tz not in _sig:
        try:
            z=ZoneInfo(tz); off=lambda d:int(d.replace(tzinfo=z).utcoffset().total_seconds()//60)
            _sig[tz]=(off(JAN),off(JUL))
        except Exception: _sig[tz]=(9999,9999)
    return _sig[tz]
if not os.path.exists("cities1000.txt"):
    d=urllib.request.urlopen("https://download.geonames.org/export/dump/cities1000.zip",timeout=300).read()
    zipfile.ZipFile(io.BytesIO(d)).extractall(".")
if not os.path.exists("countryInfo.txt"):
    urllib.request.urlretrieve("https://download.geonames.org/export/dump/countryInfo.txt","countryInfo.txt")

names={}
for line in open("countryInfo.txt",encoding="utf-8"):
    if line.startswith("#"): continue
    f=line.split("\t")
    if len(f)>4 and f[0]: names[f[0]]=f[4]

by=collections.defaultdict(list)
for r in csv.reader(open("cities1000.txt",encoding="utf-8"),delimiter="\t"):
    if len(r)<18 or r[8] not in names: continue
    try: pop=int(r[14] or 0)
    except ValueError: pop=0
    if pop<5000: continue
    by[r[8]].append((pop,r[1],r[17]))

out={}
for cc,rows in by.items():
    rows.sort(reverse=True)
    zones=collections.defaultdict(int)
    for pop,_,tz in rows: zones[sig(tz)]+=pop      # group by REAL utc offset, not zone id
    ordered=sorted(zones,key=lambda z:-zones[z])
    picked=[]
    for i,sg in enumerate(ordered):
        city=next(c for c in rows if sig(c[2])==sg)
        # the main zone always counts; extra zones need a city people have heard of
        if i>0 and city[0]<150000: continue
        picked.append([city[1],city[2]])
        if len(picked)>=4: break
    if len(picked)<3:                               # single-zone country: top cities by population
        for pop,city,tz in rows:
            if len(picked)>=3: break
            if all(city!=p[0] for p in picked): picked.append([city,tz])
    out[names[cc].lower()]=[names[cc],cc,picked]

ALIAS={"usa":"united states","us":"united states","u.s.":"united states","america":"united states",
 "uk":"united kingdom","u.k.":"united kingdom","britain":"united kingdom","great britain":"united kingdom",
 "england":"united kingdom","uae":"united arab emirates","holland":"netherlands","korea":"south korea",
 "russia":"russia","czechia":"czechia","ivory coast":"ivory coast"}
for a,target in ALIAS.items():
    if target in out and a not in out: out[a]=out[target]

js="const COUNTRY_CITIES = "+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";"
open(os.path.join(OUT,"country_cities.js"),"w",encoding="utf-8").write(js)
print(f"{len(out)} keys, {len(js)} bytes")
for k in ["united states","germany","brazil","canada","japan","australia","uk","usa","india"]:
    v=out.get(k)
    print(f"  {k:16} -> "+(", ".join(f"{c[0]} ({c[1].split('/')[-1]})" for c in v[2]) if v else "MISSING"))
