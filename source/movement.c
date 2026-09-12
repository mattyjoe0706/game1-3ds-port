#include "movement.h"

static const Solid course[]={
    {0,448,512,160}, {608,448,544,160}, {1264,448,784,160},
    {224,400,64,48}, {368,368,64,16}, {736,384,96,16},
    {928,416,48,32}, {976,384,48,64}, {1024,352,48,96},
    {1376,400,80,48}, {1552,368,112,16}, {1760,416,64,32}
};
const MovementLevel movement_test_level={course,sizeof(course)/sizeof(course[0]),2048,640,64,416,1968,0,0};
static float approach(float v,float target,float amount) {
    if(v<target) return v+amount>target?target:v+amount;
    return v-amount<target?target:v-amount;
}
static int overlaps(float a,float size,float b,float other) { return a<b+other&&a+size>b; }
void player_reset(Player *p,const MovementLevel *l) {
    *p=(Player){0}; p->x=l->spawn_x; p->y=l->spawn_y; p->height=32;
    p->head_hit=-1;
}
void player_power(Player *p,const MovementLevel *l,unsigned power) {
    float feet=p->y+p->height, height=power==POWER_SMALL?16:32;
    p->powered_rules=1;p->power=power;p->crouched=0;
    if(height>p->height) for(unsigned i=0;i<l->count;i++) {
        const Solid *s=&l->solids[i];
        if(s->w>0&&overlaps(p->x,16,s->x,s->w)&&overlaps(feet-height,height,s->y,s->h)) {
            height=16;p->crouched=1;break;
        }
    }
    p->height=height;p->y=feet-height;p->propeller_used=0;
}
void player_damage(Player *p,const MovementLevel *l) {
    if(p->invincible_ticks||p->respawn_ticks) return;
    if(p->powered_rules&&p->power!=POWER_SMALL) {
        player_power(p,l,p->power==POWER_SUPER?POWER_SMALL:POWER_SUPER);
        p->invincible_ticks=127;
    } else { p->deaths++;p->respawn_ticks=45;p->vx=p->vy=0; }
}
float player_camera_x(const Player *p,const MovementLevel *l,float view_width) {
    float max=l->width>view_width?l->width-view_width:0;
    float x=p->x+8-view_width*0.35f;
    return x<0?0:(x>max?max:x);
}
void player_step(Player *p,const MovementLevel *l,const Actions *a) {
    if(a->paused||p->finished) return;
    p->head_hit=-1;
    if(p->invincible_ticks) p->invincible_ticks--;
    if(p->respawn_ticks) {
        if(!--p->respawn_ticks) {
            unsigned deaths=p->deaths; player_reset(p,l); p->deaths=deaths;
        }
        return;
    }
    if(a->move_y>0&&p->grounded&&!p->crouched&&(!p->powered_rules||p->power!=POWER_SMALL)) {
        p->y+=16; p->height=16; p->crouched=1;
    } else if(a->move_y<=0&&p->crouched) {
        int blocked=0;
        for(unsigned i=0;i<l->count;i++) {
            const Solid *s=&l->solids[i];
            if(s->w>0&&overlaps(p->x,16,s->x,s->w)&&overlaps(p->y-16,32,s->y,s->h)) blocked=1;
        }
        if(!blocked) { p->y-=16; p->height=32; p->crouched=0; }
    }
    int was_grounded=p->grounded;
    if(p->grounded) p->propeller_used=0;
    float speed=p->crouched?1.0f:(a->run_fire?4.0f:2.25f);
    p->vx=approach(p->vx,a->move_x*speed,a->move_x?0.4f:0.5f);
    if(a->jump_pressed&&p->grounded) { p->vy=-9.4f; p->grounded=0; was_grounded=0; }
    if(!a->jump_held&&p->vy< -3.5f&&!p->propeller_used) p->vy=-3.5f;
    if(a->spin&&p->powered_rules&&p->power==POWER_PROPELLER&&!p->propeller_used) {
        p->vy=-12;p->grounded=0;was_grounded=0;p->propeller_used=1;
    }
    p->vy+=0.4f; if(p->vy>10) p->vy=10;
    if(p->power==POWER_PROPELLER&&p->propeller_used&&p->vy>2.0f&&a->move_y<=0) p->vy=2.0f;
    body_move(p,l,was_grounded);
    if(p->y>l->death_y) { p->deaths++; p->respawn_ticks=45; p->vx=p->vy=0; }
    if(!p->respawn_ticks&&p->grounded&&p->x+16>=l->goal_x) { p->finished=1; p->vx=p->vy=0; }
}

void body_move(Player *p,const MovementLevel *l,int was_grounded) {
    p->head_hit=-1;
    float nx=p->x+p->vx;
    for(unsigned i=0;i<l->count;i++) {
        const Solid *s=&l->solids[i];
        if(s->w<=0) continue;
        if(!overlaps(p->y,p->height,s->y,s->h)) continue;
        /* Permit the small rise from a ramp onto its adjoining flat tile. */
        if(was_grounded&&p->on_slope&&p->y+p->height-s->y<=4.01f) continue;
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
        if(s->w<=0) continue;
        if(!overlaps(p->x,16,s->x,s->w)) continue;
        float allowance=was_grounded&&p->on_slope?4.01f:0;
        if(p->vy>=0&&p->y+p->height<=s->y+allowance&&ny+p->height>=s->y) {
            ny=s->y-p->height; p->grounded=1;
        }
        if(p->vy<0&&p->y>=s->y+s->h&&ny<s->y+s->h) { ny=s->y+s->h;p->head_hit=(int)i; }
    }
    p->on_slope=0;
    for(unsigned i=0;i<l->surface_count;i++) {
        const Surface *s=&l->surfaces[i];
        if(!overlaps(p->x,16,s->x,s->w)||p->vy<0) continue;
        int slope=s->left!=s->right;
        float foot=p->x+8;
        /* Ramp support uses the foot centre; flat platforms use full width. */
        if(slope&&(foot<s->x||foot>=s->x+s->w)) continue;
        float t=(foot-s->x)/s->w;
        if(t<0) t=0;
        if(t>1) t=1;
        float floor=s->left+(s->right-s->left)*t;
        float old_bottom=p->y+p->height;
        float reach=was_grounded&&slope?4.01f:0;
        if(old_bottom<=floor+reach&&ny+p->height+reach>=floor&&
           (!p->grounded||floor<=ny+p->height)) {
            ny=floor-p->height; p->grounded=1; p->on_slope=slope;
        }
    }
    if(ny!=p->y+p->vy||p->grounded) p->vy=0;
    p->y=ny;
}
