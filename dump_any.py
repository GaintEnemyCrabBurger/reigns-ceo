import UnityPy, base64, os, sys
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
env = UnityPy.load(src)
for o in env.objects:
    if o.type.name != 'TextAsset':
        continue
    d = o.read()
    n = getattr(d, 'm_Name', '') or 'unnamed'
    raw = d.m_Script
    raw = bytes(raw) if not isinstance(raw, str) else raw.encode('utf-8', 'surrogateescape')
    dec = raw
    try:
        cand = base64.b64decode(raw, validate=False)
        if cand and b';' in cand[:400]:
            dec = cand
    except Exception:
        pass
    txt = dec.decode('utf-8', errors='replace')
    safe = ''.join(ch if ch.isalnum() or ch in '_-' else '_' for ch in n)
    open(os.path.join(out, safe + '.csv'), 'w', encoding='utf-8').write(txt)
    print('%-34s %8d -> %7d B  %5d lines' % (n, len(raw), len(dec), txt.count('\n') + 1))
