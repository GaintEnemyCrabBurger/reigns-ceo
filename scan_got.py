import UnityPy, base64, os, glob, sys
D = '_GoT/assets/bin/Data'
out = '_gdata'
os.makedirs(out, exist_ok=True)
files = [f for f in glob.glob(D + '/*') if not f.endswith('.resource')]
print('candidate files:', len(files))
found = 0
for f in files:
    try:
        env = UnityPy.load(f)
    except Exception:
        continue
    for o in env.objects:
        if o.type.name != 'TextAsset':
            continue
        try:
            d = o.read()
        except Exception:
            continue
        n = getattr(d, 'm_Name', '') or 'unnamed'
        raw = d.m_Script
        raw = bytes(raw) if not isinstance(raw, str) else raw.encode('utf-8', 'surrogateescape')
        dec = raw
        try:
            cand = base64.b64decode(raw, validate=False)
            if cand and b';' in cand[:500]:
                dec = cand
        except Exception:
            pass
        txt = dec.decode('utf-8', errors='replace')
        safe = ''.join(ch if ch.isalnum() or ch in '_-' else '_' for ch in n)
        open(os.path.join(out, safe + '.csv'), 'w', encoding='utf-8').write(txt)
        print('%-28s %8d -> %7d B  %5d lines' % (n, len(raw), len(dec), txt.count('\n') + 1))
        found += 1
print('total TextAssets:', found)
