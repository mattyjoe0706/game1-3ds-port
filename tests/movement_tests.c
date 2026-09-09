#include "movement.h"
#define CHECK(x) do { if(!(x)) return __LINE__; } while(0)
int run_movement_tests(void) {
    const Solid solids[]={{0,100,1000,64},{100,40,16,60},{200,20,100,16}};
    const MovementLevel l={solids,3,1000,250,20,68,950,0,0};
    Player p; Actions a={0};
    player_reset(&p,&l);
    for(int i=0;i<120;i++) player_step(&p,&l,&a);
    CHECK(p.grounded&&p.y==68);
    a.move_x=1; a.run_fire=1;
    for(int i=0;i<100;i++) player_step(&p,&l,&a);
    CHECK(p.x==84&&p.vx==0); /* Wall stops a full-speed run. */
    float x=p.x,y=p.y;
    a.paused=1; a.jump_pressed=1; a.jump_held=1;
    player_step(&p,&l,&a); CHECK(p.x==x&&p.y==y);
    player_reset(&p,&l); a=(Actions){0}; player_step(&p,&l,&a);
    a.jump_pressed=1; a.jump_held=1; player_step(&p,&l,&a);
    a.jump_pressed=0;
    float high=p.y;
    for(int i=0;i<80;i++) { player_step(&p,&l,&a); if(p.y<high) high=p.y; }
    CHECK(p.grounded&&p.y==68); /* Holding does not repeat a jump. */
    player_reset(&p,&l); a=(Actions){0}; player_step(&p,&l,&a);
    a.jump_pressed=1; a.jump_held=1; player_step(&p,&l,&a);
    a.jump_pressed=a.jump_held=0;
    float low=p.y;
    for(int i=0;i<80;i++) { player_step(&p,&l,&a); if(p.y<low) low=p.y; }
    CHECK(high+30<low); /* Releasing produces a shorter jump. */
    player_reset(&p,&l); p.x=220; p.y=36; p.vy=-9; a.jump_held=1;
    player_step(&p,&l,&a); CHECK(p.y==36&&p.vy==0); /* Ceiling. */
    const Solid tunnel[]={{0,100,500,64},{100,68,100,16}};
    const MovementLevel t={tunnel,2,500,250,20,68,450,0,0};
    player_reset(&p,&t); a=(Actions){0}; player_step(&p,&t,&a);
    a.move_y=1; player_step(&p,&t,&a); CHECK(p.crouched&&p.y==84);
    p.x=120; a.move_y=0; player_step(&p,&t,&a); CHECK(p.crouched&&p.height==16);
    p.x=220; player_step(&p,&t,&a); CHECK(!p.crouched&&p.y==68);
    p.y=300; player_step(&p,&t,&a); CHECK(p.deaths==1&&p.respawn_ticks==45);
    a.paused=1; player_step(&p,&t,&a); CHECK(p.respawn_ticks==45);
    a.paused=0; for(int i=0;i<45;i++) player_step(&p,&t,&a);
    CHECK(p.x==20&&p.y==68&&p.deaths==1);
    p.x=450; player_step(&p,&t,&a); CHECK(p.finished);
    a.move_x=-1; player_step(&p,&t,&a); CHECK(p.x==450);
    CHECK(player_camera_x(&p,&t,640)==0);
    player_reset(&p,&movement_test_level);
    a=(Actions){0}; a.move_x=1; a.run_fire=1; a.jump_held=1;
    for(int i=0;i<2400&&!p.finished;i++) {
        a.jump_pressed=p.grounded; player_step(&p,&movement_test_level,&a);
    }
    CHECK(p.finished); /* The authored course can be completed by the controller. */
    CHECK(player_camera_x(&p,&movement_test_level,640)<=1408);
    return 0;
}
