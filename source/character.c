#include "character.h"
static uint32_t word(const uint8_t *p) { return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
int character_header(const uint8_t *d,size_t n,uint32_t *hash) {
    if(!d||!hash||n!=32||d[0]!='N'||d[1]!='S'||d[2]!='P'||d[3]!='1') return 0;
    if(word(d+4)!=1||word(d+8)!=512||word(d+12)!=256||word(d+16)!=64||(word(d+20)!=21&&word(d+20)!=32)) return 0;
    uint32_t h=2166136261u;
    for(unsigned i=0;i<28;i++) h=(h^d[i])*16777619u;
    if(h!=word(d+28)) return 0;
    *hash=word(d+24);return 1;
}
void character_reset(CharacterAnim *a) { *a=(CharacterAnim){0,0,1}; }
void character_step(CharacterAnim *a,float vx,int grounded,int crouched,int paused,int respawning) {
    if(paused) return;
    if(respawning) { character_reset(a); return; }
    if(vx>0.05f) a->facing=1;
    else if(vx< -0.05f) a->facing=-1;
    float speed=vx<0?-vx:vx;
    unsigned state=!grounded?3u:crouched||speed<0.1f?0u:speed>2.6f?2u:1u;
    if(state!=a->state) { a->state=state;a->tick=0; }
    else a->tick=(a->tick+1)%(state==0?160u:60u);
}
unsigned character_frame(const CharacterAnim *a) {
    return a->state==3?20u:a->state==0?(a->tick%160)/40:(a->state==2?12u:4u)+(a->tick%60)*8/60;
}
unsigned character_carry_frame(const CharacterAnim *a) {
    if(a->state==3) return 30;
    if(a->state==0) return a->tick<80?21:31;
    return 22+((a->tick*(a->state==2?2u:1u))%60)*8/60;
}
