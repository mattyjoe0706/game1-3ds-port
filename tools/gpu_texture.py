"""RGBA8 packing for top-down images and ordinary Tex3DS subtexture UVs.

Tex3DS uses top=1-y/height. Its encoder visits image tiles top to bottom;
it does not vertically reverse ordinary 2D images before Morton packing.
Reference: devkitPro/tex3ds source/tex3ds.cpp, process_image and load_image.
"""
def rgba8_tiles(pixels,width,height):
    if width<=0 or height<=0 or width%8 or height%8 or len(pixels)!=width*height*4:
        raise ValueError('Invalid RGBA8 image dimensions or length')
    out=bytearray(len(pixels))
    for y in range(height):
        for x in range(width):
            morton=sum(((x>>bit)&1)<<(2*bit)|((y>>bit)&1)<<(2*bit+1) for bit in range(3))
            dst=((y//8)*(width//8)*64+(x//8)*64+morton)*4
            src=(y*width+x)*4
            out[dst:dst+4]=pixels[src:src+4][::-1]
    return bytes(out)
