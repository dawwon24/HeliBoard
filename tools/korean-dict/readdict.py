import sys,struct,unicodedata
d=open(sys.argv[1],'rb').read()
assert d[:4]==b'\x9b\xc1\x3a\xfe'
ver=struct.unpack('>H',d[4:6])[0]; hsize=struct.unpack('>I',d[8:12])[0]
print('version',ver,'header',hsize,file=sys.stderr)
words=[]
def rchar(p):
    b=d[p]
    if b<0x20:
        return (b<<16|d[p+1]<<8|d[p+2]),p+3
    return b,p+1
def walk(p,prefix):
    n=d[p]; p+=1
    if n&0x80: n=((n&0x7f)<<8)|d[p]; p+=1
    for _ in range(n):
        start=p
        flags=d[p]; p+=1
        chars=[]
        if flags&0x20:
            while d[p]!=0x1f:
                c,p=rchar(p); chars.append(c)
            p+=1
        else:
            c,p=rchar(p); chars.append(c)
        freq=None
        if flags&0x10: freq=d[p]; p+=1
        at=flags&0xC0; child=None
        if at:
            sz={0x40:1,0x80:2,0xC0:3}[at]
            raw=int.from_bytes(d[p:p+sz],'big')
            child=p+raw
            p+=sz
        word=prefix+''.join(map(chr,chars))
        if flags&0x08:
            sz=struct.unpack('>H',d[p:p+2])[0]; p+=sz  # size includes the size field
        if flags&0x04:
            while True:
                bf=d[p]; p+=1
                p+={0x10:1,0x20:2,0x30:3}.get(bf&0x30,0)
                if not bf&0x80: break
        if freq is not None: words.append((freq,word,flags))
        if child is not None: walk(child,word)
walk(hsize,'')
out=open(sys.argv[2],'w',encoding='utf-8')
for f,w,fl in words: out.write(f"{f}\t{unicodedata.normalize('NFC',w)}\t{fl:02x}\n")
print(len(words),'words',file=sys.stderr)
