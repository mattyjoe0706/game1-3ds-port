#include "terrain.h"
#define CHECK(x) do { if(!(x)) return __LINE__; } while(0)
static Terrain terrain;
static uint8_t bytes[TERRAIN_MAX_BYTES];
static Player player;
uint8_t *terrain_test_buffer(void) { return bytes; }
int terrain_test_load(unsigned n) {
    int ok=terrain_decode(&terrain,bytes,n);
    if(ok) player_reset(&player,&terrain.level);
    return ok;
}
unsigned terrain_test_count(void) { return terrain.count; }
float terrain_player_x(void) { return player.x; }
float terrain_player_y(void) { return player.y; }
unsigned terrain_player_deaths(void) { return player.deaths; }
int terrain_player_finished(void) { return player.finished; }
int terrain_player_grounded(void) { return player.grounded; }
int terrain_test_hill(unsigned n,unsigned package_hash,unsigned texture_hash) {
    return terrain_hill_decode(&terrain,bytes,n,package_hash,texture_hash);
}
unsigned terrain_test_surfaces(void) { return terrain.level.surface_count; }
void terrain_test_position(float x,float y) {
    player_reset(&player,&terrain.level); player.x=x;player.y=y;
}
void terrain_tick(int direction,int jump) {
    Actions a={0}; a.move_x=direction; a.run_fire=1; a.jump_held=jump;
    a.jump_pressed=jump&&player.grounded;
    player_step(&player,&terrain.level,&a);
}
static void put32(unsigned offset,uint32_t value) {
    for(unsigned i=0;i<4;i++) bytes[offset+i]=(uint8_t)(value>>(i*8));
}
static void checksum(unsigned size) {
    uint32_t hash=2166136261u;
    for(unsigned i=0;i<size;i++) if(i<32||i>=36) hash=(hash^bytes[i])*16777619u;
    put32(32,hash);
}
int run_terrain_tests(void) {
    for(unsigned i=0;i<sizeof(bytes);i++) bytes[i]=0;
    bytes[0]='N';bytes[1]='S';bytes[2]='T';bytes[3]='1';
    put32(4,1);put32(8,1);put32(12,640);put32(16,320);
    bytes[42]=1;bytes[45]=1;checksum(48);
    CHECK(terrain_test_load(48)&&terrain.count==1&&terrain.level.count==1);
    CHECK(!terrain_test_load(47)&&!terrain.count&&!terrain.level.count);
    CHECK(terrain_test_load(48));
    bytes[36]=1;checksum(48); /* Valid hash cannot legitimize unaligned coordinates. */
    CHECK(!terrain_test_load(48)&&!terrain.count);
    bytes[36]=0;bytes[42]=3;checksum(48);CHECK(!terrain_test_load(48));
    bytes[42]=1;checksum(48);bytes[28]^=1;CHECK(!terrain_test_load(48));
    bytes[28]^=1;checksum(48);
    for(int i=0;i<50;i++) CHECK(terrain_test_load(48)&&terrain.level.count==1);

    const Solid solids[]={{0,160,64,64},{128,128,128,96}};
    const Surface ramps[]={{64,64,160,128}};
    const MovementLevel l={solids,2,640,320,32,128,600,ramps,1};
    Player p;Actions a={0}; player_reset(&p,&l);player_step(&p,&l,&a);
    a.move_x=1;a.run_fire=1;
    for(int i=0;i<50;i++) player_step(&p,&l,&a);
    CHECK(p.x>180&&p.grounded&&p.y==96); /* Uphill to flat without a jump. */
    a.move_x=-1;
    for(int i=0;i<55;i++) player_step(&p,&l,&a);
    CHECK(p.x<64&&p.grounded&&p.y==128); /* Downhill to flat. */
    p.x=80;p.y=116;p.vx=0;p.vy=0;p.grounded=1;p.on_slope=1;
    a=(Actions){0};a.jump_pressed=1;a.jump_held=1;
    player_step(&p,&l,&a);CHECK(!p.grounded&&p.vy<0); /* Do not snap a jump to ramp. */
    const Surface ledge[]={{0,128,96,96}};
    const MovementLevel one_way={0,0,640,320,32,120,600,ledge,1};
    player_reset(&p,&one_way);p.vy=-9;a=(Actions){0};a.jump_held=1;
    for(int i=0;i<15;i++) player_step(&p,&one_way,&a);
    CHECK(p.y<64); /* Pass upward through platform. */
    for(int i=0;i<80;i++) player_step(&p,&one_way,&a);
    CHECK(p.grounded&&p.y==64); /* Land from above. */
    a.paused=1;float y=p.y;player_step(&p,&one_way,&a);CHECK(p.y==y);
    /* Synthetic continuous cap: asset-free CI coverage of optional loader. */
    terrain.level.width=1408;terrain.level.death_y=384;
    for(unsigned i=0;i<HILL_MAX_BYTES;i++) bytes[i]=0;
    put32(0,0x3148534e);put32(4,1);put32(8,123);put32(12,456);
    put32(16,568);put32(20,160);put32(24,160);
    for(unsigned i=0;i<160;i++) {
        union { float value; uint32_t bits; } f;
        f.value=648+4*i;put32(32+16*i,f.bits);
        f.value=4;put32(36+16*i,f.bits);
        f.value=160;put32(40+16*i,f.bits);put32(44+16*i,f.bits);
    }
    uint32_t h=2166136261u;
    for(unsigned i=0;i<HILL_MAX_BYTES;i++) if(i<28||i>=32) h=(h^bytes[i])*16777619u;
    put32(28,h);
    for(unsigned i=0;i<50;i++) {
        CHECK(terrain_hill_decode(&terrain,bytes,HILL_MAX_BYTES,123,456));
        CHECK(terrain.level.surface_count==terrain.base_surface_count+160);
    }
    CHECK(!terrain_hill_decode(&terrain,bytes,HILL_MAX_BYTES,124,456));
    CHECK(terrain.level.surface_count==terrain.base_surface_count);
    CHECK(!terrain_hill_decode(&terrain,bytes,HILL_MAX_BYTES-1,123,456));
    bytes[40]^=1;CHECK(!terrain_hill_decode(&terrain,bytes,HILL_MAX_BYTES,123,456));
    return 0;
}
