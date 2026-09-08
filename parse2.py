import struct, sys, re, collections, json
P = sys.argv[1]
FILT = sys.argv[2] if len(sys.argv) > 2 else 'Nerial'
d = open(P, 'rb').read()
h = struct.unpack('<66i', d[8:8 + 66 * 4])
SO = h[4]
MTH_O = h[10]
FLD_O = h[22]
TD_O, TD_S = h[38], h[39]


def s(i):
    if i < 0:
        return ''
    e = d.index(b'\x00', SO + i)
    return d[SO + i:e].decode('utf-8', 'replace')


nf = h[23] // 12
fields = []
for i in range(nf):
    o = FLD_O + i * 12
    n, t, tok = struct.unpack('<iiI', d[o:o + 12])
    fields.append(s(n))

nm = h[11] // 36
methods = []
for i in range(nm):
    o = MTH_O + i * 36
    n = struct.unpack('<i', d[o:o + 4])[0]
    methods.append(s(n))

TDSZ = 88
out = []
for i in range(TD_S // TDSZ):
    o = TD_O + i * TDSZ
    v = struct.unpack('<16i8H2I', d[o:o + TDSZ])
    name, ns = s(v[0]), s(v[1])
    if FILT not in ns:
        continue
    fs = v[8]
    fc = v[18]
    ms = v[9]
    mc = v[16]
    out.append(dict(ns=ns, name=name,
                    fields=[fields[j] for j in range(fs, fs + fc)] if fc > 0 and fs >= 0 else [],
                    methods=[methods[j] for j in range(ms, ms + mc)] if mc > 0 and ms >= 0 else []))
print('matched types: %d' % len(out))
json.dump(out, open(P + '.classes.json', 'w'), ensure_ascii=False, indent=0)
