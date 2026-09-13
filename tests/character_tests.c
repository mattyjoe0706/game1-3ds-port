#include "character.h"
#define CHECK(x) do { if(!(x)) return __LINE__; } while(0)
int run_character_tests(void) {
    const uint8_t valid[32]={78,83,80,49,1,0,0,0,0,2,0,0,0,1,0,0,64,0,0,0,21,0,0,0,0,0,0,0,0,0,0,0};
    uint8_t d[32];uint32_t h=2166136261u,hash=99;
    for(unsigned i=0;i<32;i++) d[i]=valid[i];
    for(unsigned i=0;i<28;i++) h=(h^d[i])*16777619u;
    for(unsigned i=0;i<4;i++) d[28+i]=(uint8_t)(h>>(8*i));
    CHECK(character_header(d,32,&hash)&&hash==0);
    CHECK(!character_header(d,31,&hash));d[24]^=1;CHECK(!character_header(d,32,&hash));d[24]^=1;
    d[20]=22;CHECK(!character_header(d,32,&hash));CHECK(!character_header(0,32,&hash));
    d[20]=32;h=2166136261u;
    for(unsigned i=0;i<28;i++) h=(h^d[i])*16777619u;
    for(unsigned i=0;i<4;i++) d[28+i]=(uint8_t)(h>>(8*i));
    CHECK(character_header(d,32,&hash));
    CharacterAnim a;character_reset(&a);CHECK(a.facing==1&&character_frame(&a)==0);
    character_step(&a,-2,1,0,0,0);CHECK(a.facing==-1&&character_frame(&a)==4);
    for(unsigned i=0;i<59;i++) character_step(&a,-2,1,0,0,0);
    CHECK(character_frame(&a)==11);
    character_step(&a,4,1,0,0,0);CHECK(character_frame(&a)==12&&a.facing==1);
    character_step(&a,-4,0,0,1,0);CHECK(a.facing==1&&character_frame(&a)==12);
    character_step(&a,-4,0,0,0,0);CHECK(character_frame(&a)==20&&a.facing==-1);
    character_step(&a,0,1,1,0,0);CHECK(character_frame(&a)==0&&a.facing==-1);
    character_step(&a,0,1,0,0,1);CHECK(a.facing==1&&character_frame(&a)==0);
    for(unsigned i=0;i<10000;i++) { character_step(&a,4,1,0,0,0);CHECK(character_frame(&a)>=12&&character_frame(&a)<20); }
    CHECK(character_carry_frame(&a)>=22&&character_carry_frame(&a)<30);
    character_step(&a,0,0,0,0,0);CHECK(character_carry_frame(&a)==30);
    character_step(&a,0,1,0,0,0);CHECK(character_carry_frame(&a)==21);
    return 0;
}
