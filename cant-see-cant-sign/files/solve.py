import socket,sys,random
e=65537
def is_prime(n):
    if n<2: return False
    for q in (2,3,5,7,11,13): 
        if n%q==0: return n==q
    dd,s=n-1,0
    while dd%2==0: dd//=2;s+=1
    for _ in range(40):
        a=random.randrange(2,n-1);x=pow(a,dd,n)
        if x in(1,n-1): continue
        for _ in range(s-1):
            x=x*x%n
            if x==n-1: break
        else: return False
    return True
while True:
    p=random.getrandbits(520)|(1<<519)|1
    if is_prime(p) and (p-1)%e: break
d=pow(e,-1,p-1)
s=socket.create_connection(((sys.argv[2] if len(sys.argv)>2 else '40.81.242.56'),int(sys.argv[1]) if len(sys.argv)>1 else 30419),timeout=15)
f=s.makefile('rwb',buffering=0)
buf=b''
def until(tok):
    global buf
    while tok not in buf:
        c=s.recv(4096)
        if not c: raise EOFError(buf)
        buf+=c
    i=buf.index(tok)+len(tok);r=buf[:i];buf=buf[i:];return r
until(b'N: ');s.sendall(str(p).encode()+b'\n')
bs=[]
try:
    while True:
        chunk=until(b'signature: ')
        b=int(chunk.split(b'sign this:')[1].split()[0]);bs.append(b)
        s.sendall(str(pow(b,d,p)).encode()+b'\n')
except EOFError as ex: print('tail:',ex.args[0][-200:])
re_=bs[0]*pow(ord('0'),-1,p)%p;inv=pow(re_,-1,p)
print(''.join(chr(x*inv%p) for x in bs))
