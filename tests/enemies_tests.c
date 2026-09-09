#include "enemies.h"
#include "terrain.h"
#define CHECK(x) do { if(!(x)) return __LINE__; } while(0)
static Terrain terrain;
static Enemies enemies;
static Player player;
static uint8_t terrain_bytes[TERRAIN_MAX_BYTES],enemy_bytes[ENEMY_MAX_BYTES];
uint8_t *encounter_terrain_buffer(void) { return terrain_bytes; }
uint8_t *encounter_enemy_buffer(void) { return enemy_bytes; }
int encounter_load(unsigned tn,unsigned en) {
    if(!terrain_decode(&terrain,terrain_bytes,tn)) return 0;
    if(!enemies_decode(&enemies,enemy_bytes,en,terrain_hash(terrain_bytes,tn),&terrain.level)) return 0;
    player_reset(&player,&terrain.level);return 1;
}
unsigned encounter_count(void) { return enemies.count; }
unsigned encounter_deaths(void) { return player.deaths; }
unsigned encounter_stomps(void) { return enemies.stomps; }
int encounter_finished(void) { return player.finished; }
void encounter_tick(int move,int jump) {
    Actions a={0};a.move_x=move;a.run_fire=1;a.jump_held=jump;a.jump_pressed=jump&&player.grounded;
    encounter_step(&enemies,&player,&terrain.level,&a,player_camera_x(&player,&terrain.level,640));
}
static void put(unsigned off,uint32_t n) { for(unsigned i=0;i<4;i++) enemy_bytes[off+i]=(uint8_t)(n>>(8*i)); }
static void hash(void) {
    uint32_t h=2166136261u;for(unsigned i=0;i<32;i++) if(i<20||i>=24) h=(h^enemy_bytes[i])*16777619u;
    put(20,h);
}
int run_enemies_tests(void) {
    const Solid solids[]={{0,100,1000,64},{100,40,16,60}};
    const MovementLevel l={solids,2,1000,250,20,68,950,0,0};
    for(unsigned i=0;i<sizeof(enemy_bytes);i++) enemy_bytes[i]=0;
    enemy_bytes[0]='N';enemy_bytes[1]='S';enemy_bytes[2]='E';enemy_bytes[3]='1';
    put(4,1);put(8,1);put(12,123);enemy_bytes[24]=80;enemy_bytes[26]=84;enemy_bytes[28]=20;hash();
    CHECK(enemies_decode(&enemies,enemy_bytes,32,123,&l)&&enemies.count==1);
    CHECK(!enemies_decode(&enemies,enemy_bytes,31,123,&l)&&!enemies.count);
    CHECK(!enemies_decode(&enemies,enemy_bytes,32,124,&l));
    enemy_bytes[28]=21;hash();CHECK(!enemies_decode(&enemies,enemy_bytes,32,123,&l));
    enemy_bytes[28]=20;hash();
    for(int i=0;i<100;i++) CHECK(enemies_decode(&enemies,enemy_bytes,32,123,&l)&&enemies.count==1);
    Player p;Actions a={0};player_reset(&p,&l);
    encounter_step(&enemies,&p,&l,&a,0);
    CHECK(enemies.items[0].state==1&&enemies.items[0].body.x<80);
    float x=enemies.items[0].body.x;a.paused=1;encounter_step(&enemies,&p,&l,&a,0);
    CHECK(enemies.items[0].body.x==x);a.paused=0;
    enemies.items[0].body.x=83.9f;enemies.items[0].direction=1;
    encounter_step(&enemies,&p,&l,&a,0);CHECK(enemies.items[0].direction==-1);
    enemies_reset(&enemies);p.x=80;p.y=45;p.vy=8;a.jump_held=1;
    encounter_step(&enemies,&p,&l,&a,0);
    CHECK(enemies.stomps==1&&enemies.items[0].state==2&&p.vy<0&&!p.respawn_ticks);
    a.paused=1;unsigned timer=enemies.items[0].timer;encounter_step(&enemies,&p,&l,&a,0);
    CHECK(enemies.items[0].timer==timer);a.paused=0;
    p.x=20;p.y=68;p.vy=0;
    for(int i=0;i<20;i++) encounter_step(&enemies,&p,&l,&a,0);
    CHECK(enemies.items[0].state==3&&enemies.stomps==1);
    enemies_reset(&enemies);player_reset(&p,&l);p.x=80;
    encounter_step(&enemies,&p,&l,&a,0);CHECK(p.respawn_ticks==45&&p.deaths==1);
    a.paused=1;encounter_step(&enemies,&p,&l,&a,0);CHECK(p.respawn_ticks==45);
    a.paused=0;
    for(int i=0;i<45;i++) encounter_step(&enemies,&p,&l,&a,0);
    CHECK(!p.respawn_ticks&&p.x==20&&enemies.items[0].state==0&&p.deaths==1);
    enemies.items[0].spawn_x=900;enemies_reset(&enemies);
    encounter_step(&enemies,&p,&l,&a,0);CHECK(enemies.items[0].state==0);
    encounter_step(&enemies,&p,&l,&a,500);CHECK(enemies.items[0].state==1);
    enemies.items[0].body.y=260;encounter_step(&enemies,&p,&l,&a,500);
    CHECK(enemies.items[0].state==3);
    return 0;
}
