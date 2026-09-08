import struct, sys, os, json
P='D:/code/REGINS-CEO/_unpack/assets/bin/Data/Managed/Metadata/global-metadata.dat'
d=open(P,'rb').read()
h=struct.unpack('<66i', d[8:8+66*4])
def reg(i): return h[i*2],h[i*2+1]
STR_O,STR_S = reg(2)
LIT_O,LIT_S = reg(0)
LITD_O,LITD_S = reg(1)
MTH_O,MTH_S = reg(5)
FLD_O,FLD_S = reg(11)
TD_O,TD_S   = reg(19)
IMG_O,IMG_S = reg(20)

def s(idx):
    if idx<0: return ''
    e=d.index(b'\x00',STR_O+idx)
    return d[STR_O+idx:e].decode('utf-8','replace')

TDSZ=88
ntd=TD_S//TDSZ
FSZ=12; nf=FLD_S//FSZ
MSZ=36; nm=MTH_S//MSZ

fields=[]
for i in range(nf):
    o=FLD_O+i*FSZ
    n,t,tok=struct.unpack('<iiI',d[o:o+12]); fields.append((s(n),t))
methods=[]
for i in range(nm):
    o=MTH_O+i*MSZ
    n,dt,rt=struct.unpack('<iii',d[o:o+12]); methods.append((s(n),dt))

types=[]
for i in range(ntd):
    o=TD_O+i*TDSZ
    v=struct.unpack('<16i8H2I',d[o:o+TDSZ])
    nameI,nsI,byval,decl,parent,elem,gc,flags,fldStart,mthStart,evStart,propStart,nestStart,ifStart,vtStart,ifOffStart = v[:16]
    mcount,pcount,fcount,ecount,ncount,vcount,icount,iocount = v[16:24]
    types.append(dict(i=i,name=s(nameI),ns=s(nsI),parent=parent,flags=flags,
                      fs=fldStart,fc=fcount,ms=mthStart,mc=mcount,decl=decl))
print('types=%d fields=%d methods=%d'%(ntd,nf,nm))
json.dump(dict(types=types,fields=fields,methods=methods),open('D:/code/REGINS-CEO/_meta.json','w'),ensure_ascii=False)

# string literals (game data strings live here)
lits=[]
for i in range(LIT_S//8):
    o=LIT_O+i*8
    ln,off=struct.unpack('<Ii',d[o:o+8])
    try: lits.append(d[LITD_O+off:LITD_O+off+ln].decode('utf-8','replace'))
    except: pass
open('D:/code/REGINS-CEO/_literals.txt','w',encoding='utf-8').write('\n'.join(lits))
print('literals=%d'%len(lits))
