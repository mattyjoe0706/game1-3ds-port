#ifndef ENEMIES_H
#define ENEMIES_H
#include "movement.h"
#define ENEMY_CAPACITY 32
#define ENEMY_MAX_BYTES (24+8*ENEMY_CAPACITY)
enum { ENEMY_DORMANT, ENEMY_WALK, ENEMY_SQUASHED, ENEMY_REMOVED,
       ENEMY_SHELL_IDLE, ENEMY_SHELL_MOVING, ENEMY_CARRIED };
typedef struct {
    Player body;
    float spawn_x,spawn_y,previous_y;
    int direction;
    unsigned state,timer;
    unsigned kind,variant,owner_grace;
} Enemy;
typedef struct { Enemy items[ENEMY_CAPACITY]; unsigned count,stomps,shell_hits; int facing; } Enemies;
int enemies_carrying(const Enemies *enemies);
int enemies_can_pickup(const Enemies *enemies,const Player *player);
void enemies_test_scene(Enemies *enemies);
extern const MovementLevel shell_test_level;
int enemies_decode(Enemies *out,const uint8_t *data,size_t n,uint32_t terrain_hash,const MovementLevel *level);
void enemies_reset(Enemies *out);
/* Whole gameplay step, including automatic player/enemy reset after death. */
void encounter_step(Enemies *enemies,Player *player,const MovementLevel *level,const Actions *a,float camera_x);
#endif
