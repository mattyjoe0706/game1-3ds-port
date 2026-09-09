#include "enemies.h"
static unsigned u16(const uint8_t *p) { return p[0]|((unsigned)p[1]<<8); }
static uint32_t u32(const uint8_t *p) { return u16(p)|((uint32_t)u16(p+2)<<16); }
static int overlap(float x,float w,float y,float h) { return x<y+h&&x+w>y; }
void enemies_reset(Enemies *out) {
    out->stomps=0;
    for(unsigned i=0;i<out->count;i++) {
        Enemy *e=&out->items[i];
        e->body=(Player){0}; e->body.x=e->spawn_x;e->body.y=e->spawn_y;e->body.height=16;
        e->previous_y=e->spawn_y;e->state=e->timer=0;e->direction=-1;
    }
}
int enemies_decode(Enemies *out,const uint8_t *data,size_t n,uint32_t terrain_hash,const MovementLevel *l) {
    out->count=out->stomps=0;
    if(n<24||n>ENEMY_MAX_BYTES||data[0]!='N'||data[1]!='S'||data[2]!='E'||data[3]!='1'||
       u32(data+4)!=1||u32(data+12)!=terrain_hash||u32(data+16)) return 0;
    unsigned count=u32(data+8);
    if(count>ENEMY_CAPACITY||n!=24+count*8) return 0;
    uint32_t hash=2166136261u;
    for(size_t i=0;i<n;i++) if(i<20||i>=24) hash=(hash^data[i])*16777619u;
    if(hash!=u32(data+20)) return 0;
    for(unsigned i=0;i<count;i++) {
        const uint8_t *r=data+24+8*i;
        if(u16(r)+16>l->width||u16(r+2)+16>l->death_y-64||u16(r+4)!=20||u16(r+6)) return 0;
        out->items[i].spawn_x=u16(r);out->items[i].spawn_y=u16(r+2);
    }
    out->count=count;enemies_reset(out);return 1;
}
void encounter_step(Enemies *all,Player *p,const MovementLevel *l,const Actions *a,float camera_x) {
    if(a->paused||p->finished) return;
    unsigned respawning=p->respawn_ticks;
    float previous_bottom=p->y+p->height;
    player_step(p,l,a);
    if(respawning) { if(!p->respawn_ticks) enemies_reset(all); return; }
    if(p->respawn_ticks||p->finished) return;
    for(unsigned i=0;i<all->count;i++) {
        Enemy *e=&all->items[i];
        if(e->state==0) {
            if(e->spawn_x>camera_x+704||e->spawn_x+16<camera_x-64) continue;
            e->state=1;e->direction=p->x<e->body.x?-1:1;
        }
        if(e->state==2) { if(!--e->timer) e->state=3; continue; }
        if(e->state!=1) continue;
        e->previous_y=e->body.y;
        e->body.vx=e->direction*0.65f;
        e->body.vy+=0.4f;if(e->body.vy>10) e->body.vy=10;
        body_move(&e->body,l,e->body.grounded);
        if(e->body.vx==0) e->direction=-e->direction;
        if(e->body.y>l->death_y) e->state=3;
    }
    /* Reverse approaching walkers once; separating overlaps do not jitter. */
    for(unsigned i=0;i<all->count;i++) for(unsigned j=i+1;j<all->count;j++) {
        Enemy *a0=&all->items[i],*b=&all->items[j];
        if(a0->state!=1||b->state!=1||!overlap(a0->body.x,16,b->body.x,16)||
           !overlap(a0->body.y,16,b->body.y,16)) continue;
        if(a0->body.x<b->body.x&&a0->direction>0&&b->direction<0) { a0->direction=-1;b->direction=1; }
        else if(a0->body.x>=b->body.x&&a0->direction<0&&b->direction>0) { a0->direction=1;b->direction=-1; }
    }
    int hit=0,stomp=0;
    float landing=p->y;
    for(unsigned i=0;i<all->count;i++) {
        Enemy *e=&all->items[i];
        if(e->state!=1||!overlap(p->x,16,e->body.x,16)) continue;
        if(previous_bottom<=e->previous_y+1&&p->y+p->height>=e->body.y&&
           p->y+p->height-previous_bottom>=e->body.y-e->previous_y) {
            e->state=2;e->timer=20;all->stomps++;stomp=1;
            if(e->body.y-p->height<landing) landing=e->body.y-p->height;
        } else if(overlap(p->y,p->height,e->body.y,16)) hit=1;
    }
    /* A simultaneous side contact still hurts, even if another enemy was stomped. */
    if(hit) { p->deaths++;p->respawn_ticks=45;p->vx=p->vy=0; }
    else if(stomp) { p->y=landing;p->vy=a->jump_held?-7.5f:-4.5f;p->grounded=p->on_slope=0; }
}
