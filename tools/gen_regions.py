import csv, json, collections, os, io, zipfile, urllib.request, sys
HERE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(HERE,".cache"); os.makedirs(CACHE,exist_ok=True)
os.chdir(CACHE)
OUT=HERE
if not os.path.exists("cities1000.txt"):
    d=urllib.request.urlopen("https://download.geonames.org/export/dump/cities1000.zip",timeout=300).read()
    zipfile.ZipFile(io.BytesIO(d)).extractall(".")
if not os.path.exists("admin1.txt"):
    urllib.request.urlretrieve("https://download.geonames.org/export/dump/admin1CodesASCII.txt","admin1.txt")

WANT={"US":"United States","CA":"Canada"}
names={}
for r in csv.reader(open("admin1.txt",encoding="utf-8"),delimiter="\t"):
    if r and r[0][:2] in WANT: names[r[0]]=r[1]

by=collections.defaultdict(list)
for r in csv.reader(open("cities1000.txt",encoding="utf-8"),delimiter="\t"):
    if len(r)<18 or r[8] not in WANT: continue
    key=f"{r[8]}.{r[10]}"
    if key not in names: continue
    try: pop=int(r[14] or 0)
    except ValueError: pop=0
    if pop<1000: continue
    by[key].append((pop,r[1],r[17]))

out={}
for key,rows in by.items():
    rows.sort(reverse=True)
    cc=key[:2]; region=names[key]
    # top 3 cities, but ensure distinct time zones are represented first
    picked=rows[:3]
    # if the region really spans zones, swap the 3rd for a MAJOR city in another zone
    main_tz=rows[0][2]
    alt=next((r for r in rows if r[2]!=main_tz and r[0]>=200000), None)
    if alt and all(alt[2]!=p[2] for p in picked):
        picked=picked[:2]+[alt]
    out[region.lower()]=[[c,region,WANT[cc],tz,cc] for _,c,tz in picked]

js="const REGION_CITIES = "+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";"
open(os.path.join(OUT,"region_cities.js"),"w",encoding="utf-8").write(js)
print(f"{len(out)} regions, {len(js)} bytes")
for k in ["new mexico","ontario","texas","california","british columbia"]:
    print(f"  {k:20} -> {[c[0] for c in out.get(k,[])]}")
