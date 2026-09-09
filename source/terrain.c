#include "terrain.h"
static uint16_t u16(const uint8_t *p) { return p[0]|((uint16_t)p[1]<<8); }
static uint32_t u32(const uint8_t *p) { return u16(p)|((uint32_t)u16(p+2)<<16); }
uint32_t terrain_hash(const uint8_t *data,size_t length) {
    uint32_t h=2166136261u;
    for(size_t i=0;i<length;i++) h=(h^data[i])*16777619u;
    return h;
}
int terrain_decode(Terrain *out,const uint8_t *data,size_t length) {
    out->count=0; out->level=(MovementLevel){0}; out->texture_hash=0;
    if(length<36||length>TERRAIN_MAX_BYTES) return 0;
    if(data[0]!='N'||data[1]!='S'||data[2]!='T'||data[3]!='1'||u32(data+4)!=1) return 0;
    uint32_t n=u32(data+8),w=u32(data+12),h=u32(data+16),sx=u32(data+20),sy=u32(data+24);
    if(!n||n>TERRAIN_CAPACITY||length!=36+12*n||w<640||w>4096||h<64||h>1024||
       sx>w-16||sy>h-32) return 0;
    /* Hash binds dimensions, spawn, texture hash and every record. */
    uint32_t hash=2166136261u;
    for(size_t i=0;i<length;i++) if(i<32||i>=36) hash=(hash^data[i])*16777619u;
    if(hash!=u32(data+32)) return 0;
    unsigned solids=0,surfaces=0;
    for(unsigned i=0;i<n;i++) {
        const uint8_t *r=data+36+12*i;
        unsigned x=u16(r),y=u16(r+2),tile=u16(r+4),kind=r[6],left=r[7],right=r[8],layer=r[9];
        if(x+16>w||y+16>h||x%16||y%16||tile>=768||kind>2||left>16||right>16||
           layer>2||u16(r+10)||(kind&&layer!=1)) return 0;
        out->tiles[i]=(TerrainTile){(uint16_t)x,(uint16_t)y,(uint16_t)tile,(uint8_t)layer};
        if(kind==1) out->solids[solids++]=(Solid){x,y,16,16};
        if(kind==2) out->surfaces[surfaces++]=(Surface){x,16,y+left,y+right};
    }
    out->level=(MovementLevel){out->solids,solids,w,h+64,sx,sy,w-24,out->surfaces,surfaces};
    out->count=n; out->texture_hash=u32(data+28);
    return 1;
}
