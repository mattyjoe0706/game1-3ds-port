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
int encounter_attach_hill(unsigned n,unsigned th,unsigned ih) {
    return terrain_hill_decode(&terrain,terrain_bytes,n,th,ih);
}
unsigned encounter_deaths(void) { return player.deaths; }
float encounter_x(void) { return player.x; }
float encounter_y(void) { return player.y; }
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
static int run_goomba_tests(void) {
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

static int run_shell_tests(void) {
    Enemies e;Player p;Actions a={0};
    enemies_test_scene(&e);player_reset(&p,&shell_test_level);
    CHECK(e.count==3&&e.items[0].kind==57&&e.items[1].variant==1);
    e.count=1;e.items[0].state=ENEMY_WALK;
    p.x=176;p.y=105;p.vy=8;
    encounter_step(&e,&p,&shell_test_level,&a,0);
    CHECK(e.items[0].state==ENEMY_SHELL_IDLE&&p.vy<0);
    p.x=157;p.y=128;p.vy=0;p.grounded=1;
    CHECK(enemies_can_pickup(&e,&p));
    InputState input={0};a=input_step(&input,BTN_X,0,0,enemies_can_pickup(&e,&p));
    encounter_step(&e,&p,&shell_test_level,&a,0);
    CHECK(enemies_carrying(&e)&&input.carrying);
    for(int i=0;i<20;i++) {
        a=input_step(&input,BTN_X,0,0,0);encounter_step(&e,&p,&shell_test_level,&a,0);
        CHECK(enemies_carrying(&e)&&!a.throw_object&&!a.pickup);
    }
    float x=e.items[0].body.x;a.paused=1;encounter_step(&e,&p,&shell_test_level,&a,0);
    CHECK(e.items[0].body.x==x&&enemies_carrying(&e));
    a=input_step(&input,0,0,0,0);encounter_step(&e,&p,&shell_test_level,&a,0);
    CHECK(e.items[0].state==ENEMY_SHELL_MOVING&&!input.carrying&&!p.respawn_ticks);
    for(int i=0;i<5;i++) {a=input_step(&input,0,0,0,0);encounter_step(&e,&p,&shell_test_level,&a,0);CHECK(!a.pickup&&!a.throw_object);}
    e.items[0].body.x=608;e.items[0].direction=1;
    encounter_step(&e,&p,&shell_test_level,&a,0);CHECK(e.items[0].direction==-1);
    e.items[0].body.x=200;e.items[0].body.y=144;e.items[0].body.vy=0;
    p.x=195;p.y=105;p.vy=8;
    encounter_step(&e,&p,&shell_test_level,&a,0);CHECK(e.items[0].state==ENEMY_SHELL_IDLE);
    p.x=64;p.y=128;p.vy=0;e.items[0].timer=1;
    encounter_step(&e,&p,&shell_test_level,&a,0);CHECK(e.items[0].state==ENEMY_WALK);
    e.items[0].state=ENEMY_SHELL_MOVING;e.items[0].body.x=p.x;e.items[0].owner_grace=0;
    encounter_step(&e,&p,&shell_test_level,&a,0);CHECK(p.respawn_ticks&&p.deaths==1);
    enemies_test_scene(&e);player_reset(&p,&shell_test_level);e.count=2;
    e.items[0].state=ENEMY_SHELL_MOVING;e.items[0].body.x=200;e.items[0].direction=1;
    e.items[1].state=ENEMY_WALK;e.items[1].kind=20;e.items[1].body.x=217;
    encounter_step(&e,&p,&shell_test_level,&a,0);CHECK(e.items[1].state==ENEMY_REMOVED&&e.shell_hits==1);
    enemies_reset(&e);CHECK(!enemies_carrying(&e)&&e.items[0].state==ENEMY_DORMANT&&e.shell_hits==0);
    e.count=1;e.items[0].state=ENEMY_CARRIED;e.items[0].body.x=580;
    p.x=608;p.y=128;p.vy=0;a=(Actions){0};a.carry_held=1;
    encounter_step(&e,&p,&shell_test_level,&a,0);
    CHECK(e.items[0].state==ENEMY_SHELL_IDLE&&e.items[0].body.x==580);
    /* Red turns at a ledge, while green walks off it. */
    Solid ledge={0,160,200,64};
    MovementLevel cliff={&ledge,1,640,320,64,128,10000,0,0};
    for(unsigned red=0;red<2;red++) {
        enemies_test_scene(&e);e.count=1;e.items[0].variant=red;
        e.items[0].state=ENEMY_WALK;e.items[0].direction=1;
        e.items[0].body.x=190;e.items[0].body.grounded=1;
        player_reset(&p,&cliff);a=(Actions){0};
        encounter_step(&e,&p,&cliff,&a,0);
        CHECK(e.items[0].direction==(red?-1:1));
    }
    return 0;
}
static int run_held_approach_tests(void) {
    /* Real input/movement loop: press X out of range and approach from either side. */
    for(int direction=-1;direction<=1;direction+=2) for(int run=0;run<2;run++)
    for(int offset=0;offset<8;offset++) {
        Enemies e;Player p;InputState input={0};Actions a;
        enemies_test_scene(&e);e.count=1;
        e.items[0].state=ENEMY_SHELL_IDLE;e.items[0].timer=511;
        e.items[0].body.x=300;
        player_reset(&p,&shell_test_level);p.x=300-direction*(80+offset*0.5f);
        uint32_t buttons=BTN_X|(direction>0?BTN_RIGHT:BTN_LEFT)|(run?BTN_Y:0);
        for(int tick=0;tick<100&&!enemies_carrying(&e);tick++) {
            input.carrying=enemies_carrying(&e);
            a=input_step(&input,buttons,0,0,enemies_can_pickup(&e,&p));
            encounter_step(&e,&p,&shell_test_level,&a,0);
            CHECK(e.items[0].state!=ENEMY_SHELL_MOVING&&!p.respawn_ticks);
        }
        CHECK(enemies_carrying(&e));
        for(int tick=0;tick<30;tick++) {
            input.carrying=enemies_carrying(&e);
            a=input_step(&input,BTN_X,0,0,enemies_can_pickup(&e,&p));
            encounter_step(&e,&p,&shell_test_level,&a,0);
            CHECK(enemies_carrying(&e)&&!a.pickup&&!a.throw_object);
        }
        a=input_step(&input,0,0,0,0);
        encounter_step(&e,&p,&shell_test_level,&a,0);
        CHECK(a.throw_object&&e.items[0].state==ENEMY_SHELL_MOVING);
        CHECK(e.items[0].direction==direction&&!p.respawn_ticks);
    }
    return 0;
}
int run_enemies_tests(void) {
    int r=run_goomba_tests();if(r)return r;
    r=run_shell_tests();return r?r:run_held_approach_tests();
}
