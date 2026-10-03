from PIL import Image;import numpy as np,glob,itertools
fs=sorted(glob.glob('pieces/*.png'));P=[np.asarray(Image.open(f).convert('RGB')).astype(float) for f in fs]
n=len(P)
def lr(a,b): return np.abs(a[:,-1]-b[:,0]).mean()
def tb(a,b): return np.abs(a[-1]-b[0]).mean()
LR=np.array([[lr(P[i],P[j]) if i!=j else 1e9 for j in range(n)] for i in range(n)])
TB=np.array([[tb(P[i],P[j]) if i!=j else 1e9 for j in range(n)] for i in range(n)])
best=None
for R,C in [(3,4),(4,3),(2,6),(6,2)]:
  # greedy from each start + beam
  beams=[((),0)]
  for k in range(R*C):
    r,c=divmod(k,C);nb=[]
    for g,s in beams:
      for j in range(n):
        if j in g: continue
        cost=s+(LR[g[k-1],j] if c else 0)+(TB[g[k-C],j] if r else 0)
        nb.append((g+(j,),cost))
    nb.sort(key=lambda x:x[1]);beams=nb[:5000]
  g,s=beams[0];print(R,C,s/(R*(C-1)+C*(R-1)),[fs[i][7:-4] for i in g])
  if best is None or s/(R*(C-1)+C*(R-1))<best[0]: best=(s/(R*(C-1)+C*(R-1)),R,C,g)
_,R,C,g=best
W=Image.new('RGB',(129*C,172*R))
for k,i in enumerate(g): W.paste(Image.open(fs[i]).convert('RGB'),((k%C)*129,(k//C)*172))
W.save('solved.png')
