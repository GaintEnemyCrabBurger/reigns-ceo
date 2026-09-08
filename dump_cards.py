import UnityPy, base64, os
env=UnityPy.load('D:/code/REGINS-CEO/_unpack/assets/bin/Data/data.unity3d')
os.makedirs('D:/code/REGINS-CEO/_data',exist_ok=True)
for o in env.objects:
    if o.type.name!='TextAsset': continue
    d=o.read(); n=getattr(d,'m_Name','')
    raw=d.m_Script
    raw=bytes(raw) if not isinstance(raw,str) else raw.encode('utf-8','surrogateescape')
    try: dec=base64.b64decode(raw, validate=False)
    except Exception: dec=raw
    txt=dec.decode('utf-8',errors='replace')
    open('D:/code/REGINS-CEO/_data/%s.csv'%n,'w',encoding='utf-8').write(txt)
    print('%-30s %8d -> %8d bytes, %d lines'%(n,len(raw),len(dec),txt.count('\n')+1))
