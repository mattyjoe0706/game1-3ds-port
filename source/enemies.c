#include "enemies.h"
static unsigned u16(const uint8_t *p) { return p[0]|((unsigned)p[1]<<8); }
static uint32_t u32(const uint8_t *p) { return u16(p)|((uint32_t)u16(p+2)<<16); }
static int overlap(float x,float w,float y,float h) { return x<y+h&&x+w>y; }
static const Solid shell_floor[]={{0,160,640,64},{0,0,16,160},{624,0,16,160}};
const MovementLevel shell_test_level={shell_floor,3,640,320,64,128,10000,0,0};
/* Source sleep timer is 511 updates; kick speed/collision sizes are provisional. */
#define SHELL_SLEEP 511u
#define SHELL_SPEED 5.0f
int enemies_carrying(const Enemies *all) {
    for(unsigned i=0;i<all->count;i++) if(all->items[i].state==ENEMY_CARRIED) return 1;
    return 0;
}
static int pickup_index(const Enemies *all,const Player *p) {
    if(p->respawn_ticks||p->finished||enemies_carrying(all)) return -1;
    for(unsigned i=0;i<all->count;i++) {
        const Enemy *e=&all->items[i];
        if(e->state==ENEMY_SHELL_IDLE&&overlap(p->x-4,24,e->body.x,16)&&
           overlap(p->y,p->height,e->body.y,16)) return (int)i;
    }
    return -1;
}
int enemies_can_pickup(const Enemies *all,const Player *p) { return pickup_index(all,p)>=0; }
void enemies_test_scene(Enemies *all) {
    *all=(Enemies){0};all->count=3;
    for(unsigned i=0;i<3;i++) {
        all->items[i].kind=i==2?20:57;all->items[i].variant=i==1;
        all->items[i].spawn_x=176+i*144;all->items[i].spawn_y=144;
    }
    enemies_reset(all);
}
static void kick(Enemy *e,int direction) {
    e->state=ENEMY_SHELL_MOVING;e->direction=direction;e->timer=0;e->owner_grace=4;
}
static void drop_carried(Enemies *all) {
    for(unsigned i=0;i<all->count;i++) if(all->items[i].state==ENEMY_CARRIED) {
        all->items[i].state=ENEMY_SHELL_IDLE;all->items[i].timer=SHELL_SLEEP;
    }
}
void enemies_reset(Enemies *out) {
    out->stomps=out->shell_hits=0;out->facing=1;
    for(unsigned i=0;i<out->count;i++) {
        Enemy *e=&out->items[i];
        e->body=(Player){0}; e->body.x=e->spawn_x;e->body.y=e->spawn_y;e->body.height=16;
        e->previous_y=e->spawn_y;e->state=e->timer=e->owner_grace=0;e->direction=-1;
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
        if(u16(r)+16>l->width||u16(r+2)+16>l->death_y-64||
           (u16(r+4)!=20&&u16(r+4)!=57)||u16(r+6)>(u16(r+4)==57?1u:0u)) return 0;
        out->items[i].spawn_x=u16(r);out->items[i].spawn_y=u16(r+2);
        out->items[i].kind=u16(r+4);out->items[i].variant=u16(r+6);
    }
    out->count=count;enemies_reset(out);return 1;
}
void encounter_step(Enemies *all,Player *p,const MovementLevel *l,const Actions *a,float camera_x) {
    if(a->paused||p->finished) return;
    if(a->move_x) all->facing=a->move_x>0?1:-1;
    int pickup=a->pickup?pickup_index(all,p):-1;
    if(pickup>=0) all->items[pickup].state=ENEMY_CARRIED;
    unsigned respawning=p->respawn_ticks;
    float previous_bottom=p->y+p->height;
    player_step(p,l,a);
    if(respawning) { if(!p->respawn_ticks) enemies_reset(all); return; }
    if(p->respawn_ticks||p->finished) {drop_carried(all);return;}
    for(unsigned i=0;i<all->count;i++) {
        Enemy *e=&all->items[i];
        if(e->state==0) {
            if(e->spawn_x>camera_x+704||e->spawn_x+16<camera_x-64) continue;
            e->state=1;e->direction=p->x<e->body.x?-1:1;
        }
        if(e->state==2) { if(!--e->timer) e->state=3; continue; }
        if(e->state==ENEMY_CARRIED) {
            float x=p->x+(all->facing>0?17:-17),y=p->y+p->height-16;
            int blocked=0;
            for(unsigned j=0;j<l->count;j++) {
                const Solid *s=&l->solids[j];
                if(overlap(x,16,s->x,s->w)&&overlap(y,16,s->y,s->h)) blocked=1;
            }
            /* Keep the last safe position instead of throwing through a wall. */
            if(blocked) {e->state=ENEMY_SHELL_IDLE;e->timer=SHELL_SLEEP;continue;}
            e->body.x=x;e->body.y=y;
            e->body.vx=e->body.vy=0;
            if(a->throw_object||!a->carry_held) kick(e,all->facing);
            else continue;
        }
        if(e->state!=ENEMY_WALK&&e->state!=ENEMY_SHELL_IDLE&&e->state!=ENEMY_SHELL_MOVING) continue;
        if(e->owner_grace) e->owner_grace--;
        if(e->state==ENEMY_SHELL_IDLE&&e->timer&&!--e->timer) e->state=ENEMY_WALK;
        e->previous_y=e->body.y;
        if(e->kind==57&&e->variant==1&&e->state==ENEMY_WALK&&e->body.grounded) {
            Player probe=e->body;probe.x+=e->direction*16;probe.vx=0;probe.vy=1;
            body_move(&probe,l,1);if(!probe.grounded) e->direction=-e->direction;
        }
        e->body.vx=e->state==ENEMY_SHELL_IDLE?0:e->direction*(e->state==ENEMY_SHELL_MOVING?SHELL_SPEED:e->kind==57?0.5f:0.65f);
        e->body.vy+=0.4f;if(e->body.vy>10) e->body.vy=10;
        body_move(&e->body,l,e->body.grounded);
        if(e->body.vx==0&&e->state!=ENEMY_SHELL_IDLE) e->direction=-e->direction;
        if(e->body.y>l->death_y) e->state=3;
    }
    /* Moving shells defeat walkers. Pairwise processing makes shell collisions symmetric. */
    for(unsigned i=0;i<all->count;i++) for(unsigned j=i+1;j<all->count;j++) {
        Enemy *a0=&all->items[i],*b=&all->items[j];
        if(!overlap(a0->body.x,16,b->body.x,16)||!overlap(a0->body.y,16,b->body.y,16)) continue;
        if(a0->state==ENEMY_SHELL_MOVING&&b->state==ENEMY_SHELL_MOVING) {
            a0->state=b->state=ENEMY_REMOVED;all->shell_hits+=2;
        } else if(a0->state==ENEMY_SHELL_MOVING&&(b->state==ENEMY_WALK||b->state==ENEMY_SHELL_IDLE)) {
            b->state=ENEMY_REMOVED;all->shell_hits++;
        } else if(b->state==ENEMY_SHELL_MOVING&&(a0->state==ENEMY_WALK||a0->state==ENEMY_SHELL_IDLE)) {
            a0->state=ENEMY_REMOVED;all->shell_hits++;
        }
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
        if((e->state!=ENEMY_WALK&&e->state!=ENEMY_SHELL_IDLE&&e->state!=ENEMY_SHELL_MOVING)||!overlap(p->x,16,e->body.x,16)) continue;
        if(previous_bottom<=e->previous_y+1&&p->y+p->height>=e->body.y&&
           p->y+p->height-previous_bottom>=e->body.y-e->previous_y) {
            if(e->kind==57) {
                if(e->state==ENEMY_SHELL_IDLE) kick(e,p->x<e->body.x?1:-1);
                else {e->state=ENEMY_SHELL_IDLE;e->timer=SHELL_SLEEP;e->body.vx=0;}
            } else {e->state=2;e->timer=20;}
            all->stomps++;stomp=1;
            if(e->body.y-p->height<landing) landing=e->body.y-p->height;
        } else if(overlap(p->y,p->height,e->body.y,16)) {
            if(e->state==ENEMY_SHELL_IDLE) kick(e,p->x<e->body.x?1:-1);
            else if(!e->owner_grace) hit=1;
        }
    }
    /* A simultaneous side contact still hurts, even if another enemy was stomped. */
    if(hit) {player_damage(p,l);drop_carried(all);}
    else if(stomp) { p->y=landing;p->vy=a->jump_held?-7.5f:-4.5f;p->grounded=p->on_slope=0; }
}
