#include "items.h"
#include "enemies.h"
#define CHECK(x) do { if(!(x)) return __LINE__; } while(0)
static Terrain t;
static Items items;
static Player player;
static Enemies foes;
static uint8_t bytes[TERRAIN_MAX_BYTES];
uint8_t *items_test_buffer(void) { return bytes; }
int items_test_terrain(unsigned n) { return terrain_decode(&t,bytes,n); }
int items_test_enemies(unsigned n,unsigned hash) {return enemies_decode(&foes,bytes,n,hash,&t.level);}
unsigned items_test_deaths(void) {return player.deaths;}
int items_test_load(unsigned n,unsigned hash) {
    int ok=items_decode(&items,bytes,n,&t,hash);
    if(ok) {player_reset(&player,&t.level);items_reset(&items,&t,&player);}
    return ok;
}
int items_test_hill(unsigned n,unsigned hash,unsigned texture) { return terrain_hill_decode(&t,bytes,n,hash,texture); }
unsigned items_test_count(void) {return items.count;}
unsigned items_test_coins(void) {return items.coins;}
unsigned items_test_power(void) {return player.power;}
unsigned items_test_block_state(unsigned i) {return i<items.count?items.blocks[i].state:999;}
void items_test_position(float x,float y) {player.x=x;player.y=y;player.vx=player.vy=0;player.grounded=0;}
void items_test_tick(int move,int jump,int spin) {
    Actions a={0};a.move_x=move;a.run_fire=1;a.jump_held=jump;a.jump_pressed=jump&&player.grounded;a.spin=spin;
    if(foes.count) encounter_step(&foes,&player,&t.level,&a,player_camera_x(&player,&t.level,640));
    else player_step(&player,&t.level,&a);
    items_step(&items,&t,&player,&a);
}
int run_items_tests(void) {
    t=(Terrain){0};items=(Items){0};t.count=3;
    t.solids[0]=(Solid){0,160,1408,64};t.solids[1]=(Solid){64,96,16,16};t.solids[2]=(Solid){96,96,16,16};
    t.level=(MovementLevel){t.solids,3,1408,384,64,128,1384,0,0};
    items.count=3;
    items.blocks[0]=(ItemBlock){.x=64,.y=96,.kind=ITEM_QUESTION,.contents=7,.solid_index=1};
    items.blocks[1]=(ItemBlock){.x=96,.y=96,.kind=ITEM_BRICK,.solid_index=2};
    items.blocks[2]=(ItemBlock){.x=16,.y=144,.kind=ITEM_COIN,.solid_index=-1};
    player_reset(&player,&t.level);items_reset(&items,&t,&player);
    CHECK(player.power==POWER_SMALL&&player.height==16&&player.y==144);
    CHECK(item_reward(7,POWER_SMALL)==POWER_PROPELLER&&item_reward(7,POWER_SUPER)==POWER_PROPELLER);
    CHECK(item_reward(7,POWER_PROPELLER)==POWER_PROPELLER);
    CHECK(item_reward(99,POWER_SMALL)==-1);
    Actions a={0};
    items.pickups[0]=(Pickup){.state=2,.kind=POWER_SUPER,.direction=1,.body={.x=64,.y=144,.height=16}};
    items_step(&items,&t,&player,&a);CHECK(player.power==POWER_SUPER);
    player_power(&player,&t.level,POWER_PROPELLER);
    items.pickups[0]=(Pickup){.state=2,.kind=POWER_SUPER,.direction=1,.body={.x=64,.y=144,.height=16}};
    items_step(&items,&t,&player,&a);CHECK(player.power==POWER_PROPELLER); /* No mushroom downgrade. */
    items_reset(&items,&t,&player);
    player_step(&player,&t.level,&a);
    a.jump_pressed=a.jump_held=1;player_step(&player,&t.level,&a);items_step(&items,&t,&player,&a);
    a.jump_pressed=0;
    for(unsigned i=0;i<30;i++){player_step(&player,&t.level,&a);items_step(&items,&t,&player,&a);}
    CHECK(items.blocks[0].state==1); /* Real head contact activates exactly once. */
    unsigned age=items.pickups[0].age;a.paused=1;items_step(&items,&t,&player,&a);
    CHECK(items.pickups[0].age==age);a.paused=0;
    for(unsigned i=0;i<40;i++) items_step(&items,&t,&player,&a);
    CHECK(items.pickups[0].state==2);
    player.x=items.pickups[0].body.x;player.y=items.pickups[0].body.y;
    items_step(&items,&t,&player,&a);
    CHECK(player.power==POWER_PROPELLER&&items.collected==1&&!items.pickups[0].state);
    player.x=200;player.y=128;player.grounded=1;player.vy=0;a=(Actions){0};a.spin=1;
    player_step(&player,&t.level,&a);CHECK(player.vy< -10&&player.propeller_used&&!player.grounded);
    float speed=player.vy;player_step(&player,&t.level,&a);CHECK(player.vy>speed); /* No repeated boost. */
    a.paused=1;float y=player.y;player_step(&player,&t.level,&a);CHECK(player.y==y);
    player_damage(&player,&t.level);CHECK(player.power==POWER_SUPER&&player.invincible_ticks==127);
    player_damage(&player,&t.level);CHECK(player.power==POWER_SUPER);
    player.invincible_ticks=0;player_damage(&player,&t.level);CHECK(player.power==POWER_SMALL&&player.height==16);
    player.invincible_ticks=0;player_damage(&player,&t.level);CHECK(player.deaths==1&&player.respawn_ticks);
    a=(Actions){0};items_step(&items,&t,&player,&a);CHECK(!items.blocks[0].state&&!items.collected);
    for(int i=0;i<45;i++){player_step(&player,&t.level,&a);items_step(&items,&t,&player,&a);}
    CHECK(player.powered_rules&&player.power==POWER_SMALL&&player.height==16&&!player.respawn_ticks);
    player.x=16;player.y=144;items_step(&items,&t,&player,&a);items_step(&items,&t,&player,&a);CHECK(items.coins==1);
    player.head_hit=2;items_step(&items,&t,&player,&a);CHECK(!items.blocks[1].state);
    player_power(&player,&t.level,POWER_SUPER);items.blocks[1].bump=0;player.head_hit=2;
    items_step(&items,&t,&player,&a);CHECK(items.blocks[1].state==2&&t.solids[2].w==0);
    items_reset(&items,&t,&player);CHECK(t.solids[2].w==16&&!items.blocks[1].state&&!items.coins);
    player.x=64;player.y=112;player.height=16;
    player_power(&player,&t.level,POWER_PROPELLER);CHECK(player.height==16&&player.crouched); /* Ceiling-safe growth. */
    return 0;
}
