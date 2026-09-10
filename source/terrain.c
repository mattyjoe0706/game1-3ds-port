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
    out->base_surface_count=0; out->hill_texture_hash=0;
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
    out->base_surface_count=surfaces;
    return 1;
}

static float f32(const uint8_t *p) {
    union { uint32_t bits; float value; } decoded;
    decoded.bits=u32(p); return decoded.value;
}
int terrain_hill_decode(Terrain *out,const uint8_t *data,size_t length,
                        uint32_t package_hash,uint32_t texture_hash) {
    out->level.surface_count=out->base_surface_count; out->hill_texture_hash=0;
    if(!out->count||out->level.width!=1408||out->level.death_y!=384||
       length!=HILL_MAX_BYTES||u32(data)!=0x3148534eu||u32(data+4)!=1||
       u32(data+8)!=package_hash||u32(data+12)!=texture_hash||u32(data+16)!=568||
       u32(data+20)!=160||u32(data+24)!=160||out->base_surface_count+160>TERRAIN_CAPACITY) return 0;
    uint32_t hash=2166136261u;
    for(size_t i=0;i<length;i++) if(i<28||i>=32) hash=(hash^data[i])*16777619u;
    if(hash!=u32(data+28)) return 0;
    float previous=0;
    for(unsigned i=0;i<160;i++) {
        const uint8_t *r=data+32+16*i;
        float x=f32(r),w=f32(r+4),left=f32(r+8),right=f32(r+12);
        if(x!=648+4*i||w!=4||!(left>=159.99f&&left<=320.01f)||
           !(right>=159.99f&&right<=320.01f)||
           (i&&left!=previous)) return 0;
        previous=right;
    }
    for(unsigned i=0;i<160;i++) {
        const uint8_t *r=data+32+16*i;
        out->surfaces[out->base_surface_count+i]=(Surface){f32(r),f32(r+4),f32(r+8),f32(r+12)};
    }
    out->level.surface_count=out->base_surface_count+160;
    out->hill_texture_hash=texture_hash;
    return 1;
}
