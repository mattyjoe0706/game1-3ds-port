#include "items.h"
static unsigned u16(const uint8_t *b) { return b[0]|((unsigned)b[1]<<8); }
static uint32_t u32(const uint8_t *b) { return u16(b)|((uint32_t)u16(b+2)<<16); }
static int overlap(float a,float w,float b,float h) { return a<b+h&&a+w>b; }
int item_reward(unsigned contents,unsigned power) {
    (void)power;
    /* Pa0 object extra: 0=coin, 7=Propeller. Propeller is a direct upgrade,
       including from small; do not replace it with a Mushroom. Other original
       content types need their own verified selection rules before enabling. */
    if(contents==0) return 0;
    if(contents==7) return POWER_PROPELLER;
    return -1;
}
int items_decode(Items *o,const uint8_t *b,size_t n,Terrain *t,uint32_t th) {
    o->count=0;o->texture_hash=0;
    if(n<24||n>ITEM_MAX_BYTES||u32(b)!=0x3149534e||u32(b+4)!=1||u32(b+12)!=th) return 0;
    unsigned count=u32(b+8);
    if(count>ITEM_CAPACITY||n!=24+count*12) return 0;
    uint32_t hash=2166136261u;
    for(size_t i=0;i<n;i++) if(i<20||i>=24) hash=(hash^b[i])*16777619u;
    if(hash!=u32(b+20)) return 0;
    for(unsigned i=0;i<count;i++) {
        const uint8_t *r=b+24+12*i;
        ItemBlock v={0};v.x=u16(r);v.y=u16(r+2);v.tile_index=u16(r+4);
        v.kind=r[6];v.contents=r[7];v.solid_index=-1;
        if(v.x>=t->level.width||v.y+16>t->level.death_y-64||u32(r+8)||
           (v.kind!=ITEM_COIN&&v.x+16>t->level.width)||
           v.kind<1||v.kind>3|| (v.kind!=ITEM_QUESTION&&v.contents)||
           (v.kind==ITEM_QUESTION&&v.contents!=0&&v.contents!=7)) return 0;
        if(v.tile_index!=65535) {
            if(v.tile_index>=t->count) return 0;
            const TerrainTile *tile=&t->tiles[v.tile_index];
            unsigned expected=v.kind==ITEM_COIN?30:v.kind==ITEM_BRICK?48:49;
            if(tile->x!=v.x||tile->y!=v.y||tile->tile!=expected||tile->layer!=1) return 0;
        } else if(v.kind!=ITEM_COIN) return 0;
        for(unsigned j=0;j<i;j++) if(o->blocks[j].x==v.x&&o->blocks[j].y==v.y) return 0;
        if(v.kind!=ITEM_COIN) {
            for(unsigned j=0;j<t->level.count;j++) if(t->solids[j].x==v.x&&t->solids[j].y==v.y&&t->solids[j].w==16) v.solid_index=(int)j;
            if(v.solid_index<0) return 0;
        }
        o->blocks[i]=v;
    }
    o->count=count;o->texture_hash=u32(b+16);return 1;
}
void items_reset(Items *o,Terrain *t,Player *p) {
    o->coins=o->collected=0;o->last_deaths=p->deaths;
    for(unsigned i=0;i<o->count;i++) {
        ItemBlock *v=&o->blocks[i];v->state=v->bump=0;
        if(v->solid_index>=0) t->solids[v->solid_index].w=16;
    }
    for(unsigned i=0;i<ITEM_POOL;i++) o->pickups[i]=(Pickup){0};
    player_power(p,&t->level,POWER_SMALL);
}
void items_step(Items *o,Terrain *t,Player *p,const Actions *a) {
    if(a->paused||p->finished) return;
    if(p->deaths!=o->last_deaths) { items_reset(o,t,p);return; }
    if(p->respawn_ticks) return;
    if(!p->powered_rules) player_power(p,&t->level,POWER_SMALL);
    for(unsigned i=0;i<o->count;i++) {
        ItemBlock *v=&o->blocks[i];if(v->bump) v->bump--;
        if(v->state) continue;
        if(v->kind==ITEM_COIN) {
            if(overlap(p->x,16,v->x,16)&&overlap(p->y,p->height,v->y,16)) { v->state=1;o->coins++; }
        } else if(p->head_hit==v->solid_index&&!v->bump) {
            v->bump=12;
            if(v->kind==ITEM_BRICK) {
                if(p->power!=POWER_SMALL) { v->state=2;t->solids[v->solid_index].w=0; }
            } else {
                int reward=item_reward(v->contents,p->power);
                if(!reward) { v->state=1;o->coins++; }
                else {
                    for(unsigned k=0;k<ITEM_POOL;k++) if(!o->pickups[k].state) {
                        Pickup *q=&o->pickups[k];*q=(Pickup){0};q->state=1;q->kind=(unsigned)reward;
                        q->body.x=v->x;q->body.y=v->y;q->body.height=16;q->origin_y=v->y;
                        q->direction=p->x+8<v->x+8?1:-1;
                        v->state=1;break;
                    }
                }
            }
        }
    }
    p->head_hit=-1;
    for(unsigned i=0;i<ITEM_POOL;i++) {
        Pickup *q=&o->pickups[i];if(!q->state) continue;
        q->age++;
        if(q->state==1) {
            q->body.y=q->origin_y-q->age*0.5f;
            if(q->age>=32) {q->state=2;q->age=0;q->body.vy=q->kind==POWER_PROPELLER?-2.5f:0;}
            continue;
        }
        q->body.vx=q->direction*(q->kind==POWER_PROPELLER?0.8f:1.2f);
        q->body.vy+=q->kind==POWER_PROPELLER?0.08f:0.4f;
        if(q->body.vy>4) q->body.vy=4;
        body_move(&q->body,&t->level,q->body.grounded);
        if(!q->body.vx) q->direction=-q->direction;
        if(q->kind==POWER_PROPELLER&&q->body.grounded) q->body.vy=-2.5f;
        if(overlap(p->x,16,q->body.x,16)&&overlap(p->y,p->height,q->body.y,16)) {
            if(q->kind!=POWER_SUPER||p->power==POWER_SMALL) player_power(p,&t->level,q->kind);
            o->collected++;q->state=0;
        } else if(q->body.y>t->level.death_y||q->age>1800) q->state=0;
    }
}
