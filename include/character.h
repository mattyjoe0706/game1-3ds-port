#ifndef CHARACTER_H
#define CHARACTER_H
#include <stddef.h>
#include <stdint.h>
#define CHARACTER_TEXTURE_BYTES (512u*256u*4u)
typedef struct { unsigned tick,state; int facing; } CharacterAnim;
int character_header(const uint8_t *data,size_t size,uint32_t *texture_hash);
void character_reset(CharacterAnim *a);
void character_step(CharacterAnim *a,float vx,int grounded,int crouched,int paused,int respawning);
unsigned character_frame(const CharacterAnim *a);
unsigned character_carry_frame(const CharacterAnim *a);
#endif
