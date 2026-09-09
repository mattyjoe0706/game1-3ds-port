#ifndef TERRAIN_H
#define TERRAIN_H
#include "movement.h"
#define TERRAIN_CAPACITY 2048
#define TERRAIN_MAX_BYTES (36+12*TERRAIN_CAPACITY)
#define TERRAIN_TEXTURE_BYTES (512*512*4)
typedef struct { uint16_t x,y,tile; uint8_t layer; } TerrainTile;
typedef struct {
    TerrainTile tiles[TERRAIN_CAPACITY];
    Solid solids[TERRAIN_CAPACITY];
    Surface surfaces[TERRAIN_CAPACITY];
    MovementLevel level;
    uint32_t count, texture_hash;
} Terrain;
uint32_t terrain_hash(const uint8_t *data,size_t length);
/* On rejection, count and level are cleared. Texture checked separately. */
int terrain_decode(Terrain *out,const uint8_t *data,size_t length);
#endif
