"""Decode the I8, RGB565 and CMPR texture formats used in Mario.arc."""
import struct

def rgb565(word):
    r,g,b=(word>>11)&31,(word>>5)&63,word&31
    return ((r<<3)|(r>>2),(g<<2)|(g>>4),(b<<3)|(b>>2),255)

def decode(data,width,height,kind):
    if not 0<width<=1024 or not 0<height<=1024:raise ValueError('Invalid texture dimensions')
    if kind not in (1,4,14):raise ValueError('Unsupported character texture format')
    bw,bh=(8,4) if kind==1 else (4,4) if kind==4 else (8,8)
    size=((width+bw-1)//bw)*((height+bh-1)//bh)*32
    if len(data)<size:raise ValueError('Truncated texture')
    out=bytearray(width*height*4);cursor=0
    def put(x,y,color):
        if x<width and y<height:out[(y*width+x)*4:(y*width+x+1)*4]=bytes(color)
    for by in range(0,height,bh):
        for bx in range(0,width,bw):
            if kind==14:
                for sub in range(4):
                    c0,c1,indices=struct.unpack_from('>HHI',data,cursor);cursor+=8
                    a,b=rgb565(c0),rgb565(c1)
                    palette=[a,b]
                    if c0>c1:palette.extend([tuple((2*a[i]+b[i])//3 for i in range(3))+(255,),tuple((a[i]+2*b[i])//3 for i in range(3))+(255,)])
                    else:palette.extend([tuple((a[i]+b[i])//2 for i in range(3))+(255,),(0,0,0,0)])
                    for y in range(4):
                        for x in range(4):put(bx+(sub%2)*4+x,by+(sub//2)*4+y,palette[(indices>>(30-2*(y*4+x)))&3])
            else:
                for y in range(bh):
                    for x in range(bw):
                        if kind==1:
                            value=data[cursor];cursor+=1;color=(value,value,value,255)
                        else:color=rgb565(struct.unpack_from('>H',data,cursor)[0]);cursor+=2
                        put(bx+x,by+y,color)
    return bytes(out)

def textures(reader):
    result={}
    for name,p in reader.resources().get('Textures(NW4R)',[]):
        version=reader.read('I',p+8)
        if version not in (1,3):raise ValueError('Unsupported TEX0 version')
        end=reader.section(p,b'TEX0',version)
        if p+48>end:raise ValueError('Truncated texture header')
        offset=reader.read('I',p+16);w,h,kind=reader.read('HHI',p+28)
        if offset<48 or p+offset>end:raise ValueError('Invalid texture offset')
        result[name]=(w,h,decode(reader.data[p+offset:end],w,h,kind))
    return result
