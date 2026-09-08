#include "movement.h"

static const Solid course[]={
    {0,448,512,160}, {608,448,544,160}, {1264,448,784,160},
    {224,400,64,48}, {368,368,64,16}, {736,384,96,16},
    {928,416,48,32}, {976,384,48,64}, {1024,352,48,96},
    {1376,400,80,48}, {1552,368,112,16}, {1760,416,64,32}
};
const MovementLevel movement_test_level={course,sizeof(course)/sizeof(course[0]),2048,640,64,416,1968};
static float approach(float v,float target,float amount) {
    if(v<target) return v+amount>target?target:v+amount;
    return v-amount<target?target:v-amount;
}
static int overlaps(float a,float size,float b,float other) { return a<b+other&&a+size>b; }
void player_reset(Player *p,const MovementLevel *l) {
    *p=(Player){0}; p->x=l->spawn_x; p->y=l->spawn_y; p->height=32;
}
float player_camera_x(const Player *p,const MovementLevel *l,float view_width) {
    float max=l->width>view_width?l->width-view_width:0;
    float x=p->x+8-view_width*0.35f;
    return x<0?0:(x>max?max:x);
}
void player_step(Player *p,const MovementLevel *l,const Actions *a) {
    if(a->paused||p->finished) return;
    if(p->respawn_ticks) {
        if(!--p->respawn_ticks) {
            unsigned deaths=p->deaths; player_reset(p,l); p->deaths=deaths;
        }
        return;
    }
    if(a->move_y>0&&p->grounded&&!p->crouched) {
        p->y+=16; p->height=16; p->crouched=1;
    } else if(a->move_y<=0&&p->crouched) {
        int blocked=0;
        for(unsigned i=0;i<l->count;i++) {
            const Solid *s=&l->solids[i];
            if(overlaps(p->x,16,s->x,s->w)&&overlaps(p->y-16,32,s->y,s->h)) blocked=1;
        }
        if(!blocked) { p->y-=16; p->height=32; p->crouched=0; }
    }
    float speed=p->crouched?1.0f:(a->run_fire?4.0f:2.25f);
    p->vx=approach(p->vx,a->move_x*speed,a->move_x?0.4f:0.5f);
    if(a->jump_pressed&&p->grounded) { p->vy=-9.4f; p->grounded=0; }
    if(!a->jump_held&&p->vy< -3.5f) p->vy=-3.5f;
    p->vy+=0.4f; if(p->vy>10) p->vy=10;
    float nx=p->x+p->vx;
    for(unsigned i=0;i<l->count;i++) {
        const Solid *s=&l->solids[i];
        if(!overlaps(p->y,p->height,s->y,s->h)) continue;
        if(p->vx>0&&p->x+16<=s->x&&nx+16>s->x) { nx=s->x-16; }
        if(p->vx<0&&p->x>=s->x+s->w&&nx<s->x+s->w) { nx=s->x+s->w; }
    }
    if(nx<0) nx=0;
    if(nx>l->width-16) nx=l->width-16;
    if(nx!=p->x+p->vx) p->vx=0;
    p->x=nx;
    float ny=p->y+p->vy;
    p->grounded=0;
    for(unsigned i=0;i<l->count;i++) {
        const Solid *s=&l->solids[i];
        if(!overlaps(p->x,16,s->x,s->w)) continue;
        if(p->vy>=0&&p->y+p->height<=s->y&&ny+p->height>=s->y) {
            ny=s->y-p->height; p->grounded=1;
        }
        if(p->vy<0&&p->y>=s->y+s->h&&ny<s->y+s->h) ny=s->y+s->h;
    }
    if(ny!=p->y+p->vy||p->grounded) p->vy=0;
    p->y=ny;
    if(p->y>l->death_y) { p->deaths++; p->respawn_ticks=45; p->vx=p->vy=0; }
    if(!p->respawn_ticks&&p->grounded&&p->x+16>=l->goal_x) { p->finished=1; p->vx=p->vy=0; }
}
