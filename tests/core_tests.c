#include "core.h"
#define CHECK(expr) do { if (!(expr)) return __LINE__; } while (0)
static Scene scene;
static uint8_t buffer[SCENE_MAX_BYTES];
/* Exports let the JS runner supply real converter output to the same C loader. */
uint8_t *test_buffer(void) { return buffer; }
int load_test(unsigned n) { return scene_decode(&scene,buffer,n); }
unsigned loaded_count(void) { return scene.count; }
unsigned loaded_area(void) { return scene.area; }
int loaded_x(unsigned n) { return n<scene.count ? scene.records[n].x : -1; }
unsigned loaded_id(unsigned n) { return n<scene.count ? scene.records[n].id : 0; }
int run_core_tests(void) {
    InputState s={0}; Actions a;
    a=input_step(&s,BTN_X,0,0,1); CHECK(a.pickup && a.carry_held && !a.throw_object);
    for (int i=0;i<120;i++) { a=input_step(&s,BTN_X,0,0,1); CHECK(!a.pickup&&!a.throw_object&&a.carry_held); }
    a=input_step(&s,0,0,0,1); CHECK(a.throw_object&&!a.carry_held);
    a=input_step(&s,0,0,0,1); CHECK(!a.throw_object);
    a=input_step(&s,BTN_X,0,0,0); CHECK(!a.pickup);
    a=input_step(&s,BTN_X,0,0,1); CHECK(a.pickup&&a.carry_held); /* approach while holding X */
    s.carrying=0; /* Wall drop/destruction must not cause repeated pickup. */
    a=input_step(&s,BTN_X,0,0,1); CHECK(!a.pickup&&!a.throw_object);
    input_step(&s,0,0,0,1);
    a=input_step(&s,BTN_X,0,0,1); CHECK(a.pickup);
    a=input_step(&s,BTN_X|BTN_START,0,0,1); CHECK(a.paused&&!a.pickup&&!a.throw_object);
    a=input_step(&s,0,0,0,1); CHECK(a.paused); /* X released during pause */
    a=input_step(&s,BTN_START,0,0,1); CHECK(!a.paused&&a.throw_object);
    a=input_step(&s,BTN_L|BTN_ZR,0,0,0); CHECK(a.tilt==0);
    a=input_step(&s,BTN_ZL|BTN_ZR,0,0,0); CHECK(a.tilt==0);
    a=input_step(&s,BTN_L|BTN_ZL,0,0,0); CHECK(a.tilt==-1);
    a=input_step(&s,BTN_ZR,0,0,0); CHECK(a.tilt==1);
    a=input_step(&s,BTN_A|BTN_Y|BTN_R,0,0,0); CHECK(a.jump_pressed&&a.jump_held&&a.run_fire&&a.spin);
    a=input_step(&s,BTN_A|BTN_Y|BTN_R,0,0,0); CHECK(!a.jump_pressed&&!a.spin&&a.jump_held);
    a=input_step(&s,BTN_B,0,0,0); CHECK(a.jump_pressed&&a.jump_held);
    a=input_step(&s,0,41,-41,0); CHECK(a.move_x==1&&a.move_y==1);
    a=input_step(&s,0,40,-40,0); CHECK(!a.move_x&&!a.move_y);
    a=input_step(&s,BTN_LEFT,150,0,0); CHECK(a.move_x==-1);
    a=input_step(&s,BTN_LEFT|BTN_RIGHT,150,0,0); CHECK(a.move_x==0);
    a=input_step(&s,BTN_UP|BTN_DOWN,0,150,0); CHECK(a.move_y==0);
    FixedClock c={0}; unsigned total=0;
    for(int i=0;i<120;i++) total+=clock_advance(&c,1.0/120.0);
    CHECK(total==60&&c.discarded_steps==0);
    CHECK(clock_advance(&c,0.5)==5&&c.discarded_steps==25);
    CHECK(clock_advance(&c,-1)==0);
    CHECK(clock_advance(&c,61)==5&&c.clipped_seconds==1);
    SceneRecord r={0,0,0,100,100,10,10,0};
    CHECK(scene_visible(&r,90,90,20,20));
    CHECK(!scene_visible(&r,0,0,100,100));
    CHECK(!scene_visible(&r,110,100,10,10));
    CHECK(!scene_decode(&scene,0,0));
    return 0;
}
