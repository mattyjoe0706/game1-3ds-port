#ifndef ENEMIES_H
#define ENEMIES_H
#include "movement.h"
#define ENEMY_CAPACITY 32
#define ENEMY_MAX_BYTES (24+8*ENEMY_CAPACITY)
typedef struct {
    Player body;
    float spawn_x,spawn_y,previous_y;
    int direction;
    unsigned state,timer; /* 0 dormant, 1 walking, 2 squashed, 3 removed */
} Enemy;
typedef struct { Enemy items[ENEMY_CAPACITY]; unsigned count,stomps; } Enemies;
int enemies_decode(Enemies *out,const uint8_t *data,size_t n,uint32_t terrain_hash,const MovementLevel *level);
void enemies_reset(Enemies *out);
/* Whole gameplay step, including automatic player/enemy reset after death. */
void encounter_step(Enemies *enemies,Player *player,const MovementLevel *level,const Actions *a,float camera_x);
#endif
