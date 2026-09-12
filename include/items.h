#ifndef ITEMS_H
#define ITEMS_H
#include "terrain.h"
#define ITEM_CAPACITY 128
#define ITEM_POOL 8
#define ITEM_MAX_BYTES (24+12*ITEM_CAPACITY)
enum { ITEM_COIN=1, ITEM_QUESTION=2, ITEM_BRICK=3 };
typedef struct {
    unsigned x,y,tile_index,kind,contents,state,bump;
    int solid_index;
} ItemBlock;
typedef struct { Player body; unsigned kind,state,age; int direction; float origin_y; } Pickup;
typedef struct {
    ItemBlock blocks[ITEM_CAPACITY];Pickup pickups[ITEM_POOL];
    unsigned count,coins,last_deaths,collected;
    uint32_t texture_hash;
} Items;
int items_decode(Items *out,const uint8_t *bytes,size_t size,Terrain *terrain,uint32_t terrain_hash);
void items_reset(Items *out,Terrain *terrain,Player *player);
void items_step(Items *out,Terrain *terrain,Player *player,const Actions *actions);
/* Supported source contents: 0 coin, 7 -> Propeller. Unknown definitions return -1. */
int item_reward(unsigned contents,unsigned player_power);
#endif
