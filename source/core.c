#include "core.h"

static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static uint32_t fnv1a(const uint8_t *p, size_t n) {
    uint32_t h=2166136261u;
    for (size_t i=0;i<n;i++) if (i<28 || i>=32) h=(h^p[i])*16777619u;
    return h;
}
int scene_decode(Scene *s, const uint8_t *p, size_t length) {
    if (!s) return 0;
    s->count=0;
    if (!p || length<SCENE_HEADER_SIZE || length>SCENE_MAX_BYTES) return 0;
    if (p[0]!='N'||p[1]!='S'||p[2]!='C'||p[3]!='1'||le32(p+4)!=1||le32(p+24)!=1) return 0;
    uint32_t area=le32(p+8), count=le32(p+12);
    if (area<1||area>4||!count||count>SCENE_CAPACITY) return 0;
    if (length!=SCENE_HEADER_SIZE+(size_t)count*SCENE_RECORD_SIZE) return 0;
    if (le32(p+16)>65535||le32(p+20)>65535) return 0;
    if (fnv1a(p,length)!=le32(p+28)) return 0;
    for (uint32_t i=0;i<count;i++) {
        const uint8_t *r=p+32+i*24;
        uint32_t x=le32(r+4), y=le32(r+8), w=le32(r+12), h=le32(r+16);
        if (r[0]>3||r[1]>2||x>1048560||y>1048560||!w||!h||w>1048560||h>1048560) return 0;
        s->records[i]=(SceneRecord){r[0],r[1],(uint16_t)(r[2]|(uint16_t)r[3]<<8),
                                    (int32_t)x,(int32_t)y,(int32_t)w,(int32_t)h,le32(r+20)};
    }
    s->area=area; s->start_x=le32(p+16); s->start_y=le32(p+20); s->count=count;
    return 1;
}
int scene_visible(const SceneRecord *r, float x, float y, float w, float h) {
    return r && w>0 && h>0 && r->x<x+w && r->x+r->w>x && r->y<y+h && r->y+r->h>y;
}
Actions input_step(InputState *s, uint32_t b, int px, int py, int can_pickup) {
    Actions a={0};
    uint32_t pressed=b&~s->previous;
    s->previous=b;
    if (pressed&BTN_START) s->paused=!s->paused;
    a.paused=s->paused;
    if (s->paused) return a;
    if (b&(BTN_LEFT|BTN_RIGHT)) a.move_x=!!(b&BTN_RIGHT)-!!(b&BTN_LEFT);
    else a.move_x=(px>40)-(px< -40);
    if (b&(BTN_UP|BTN_DOWN)) a.move_y=!!(b&BTN_DOWN)-!!(b&BTN_UP);
    else a.move_y=(py< -40)-(py>40);
    a.jump_pressed=!!(pressed&(BTN_A|BTN_B));
    a.jump_held=!!(b&(BTN_A|BTN_B)); a.run_fire=!!(b&(BTN_Y|BTN_X));
    a.spin=!!(pressed&BTN_R);
    a.tilt=!!(b&BTN_ZR)-!!(b&(BTN_L|BTN_ZL));
    a.carry_intent=!!(b&(BTN_Y|BTN_X));
    if (!a.carry_intent) s->pickup_used=0;
    if (s->carrying && a.carry_intent) s->pickup_used=1;
    a.pickup_armed=a.carry_intent&&!s->carrying&&!s->pickup_used;
    if (s->carrying && !a.carry_intent) { a.throw_object=1; s->carrying=0; }
    else if (a.pickup_armed && can_pickup) {
        a.pickup=1; s->carrying=1; s->pickup_used=1;
    }
    a.carry_held=s->carrying;
    return a;
}
unsigned clock_advance(FixedClock *c, double elapsed) {
    const double step=1.0/60.0;
    if (!(elapsed>=0.0)) return 0;
    /* Suspend/resume can span hours: avoid overflow and unbounded catch-up. */
    if (elapsed>60.0) { c->clipped_seconds+=elapsed-60.0; elapsed=60.0; }
    c->pending+=elapsed;
    unsigned due=(unsigned)((c->pending+1e-9)/step);
    c->pending-=due*step;
    if (c->pending<0) c->pending=0;
    if (due>5) { c->discarded_steps+=due-5; return 5; }
    return due;
}
