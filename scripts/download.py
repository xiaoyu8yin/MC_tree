import urllib.request, concurrent.futures, pathlib, json, hashlib
v=json.loads(pathlib.Path('data/version.json').read_text(encoding='utf-8-sig'))
d=v['downloads']['client']; size=d['size']; step=262144
def part(i):
    end=min(size-1,i+step-1)
    req=urllib.request.Request(d['url'],headers={'Range':f'bytes={i}-{end}'})
    for retry in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                data=r.read()
                if len(data)!=end-i+1: raise ValueError((r.status,len(data)))
                return i,data
        except Exception:
            if retry==3: raise
parts=list(concurrent.futures.ThreadPoolExecutor(32).map(part,range(0,size,step)))
data=b''.join(b for _,b in sorted(parts))
assert hashlib.sha1(data).hexdigest()==d['sha1']
pathlib.Path('data/verified.jar').write_bytes(data)
print('Verified',len(data),d['sha1'])
