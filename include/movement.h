#ifndef MOVEMENT_H
#define MOVEMENT_H
#include "core.h"

/* Authored controller test course. Not decoded Wii collision or Mario physics. */
typedef struct { float x,y,w,h; } Solid;
/* One-way floor; endpoint heights are absolute world coordinates. */
typedef struct { float x,w,left,right; } Surface;
typedef struct {
    const Solid *solids;
    unsigned count;
    float width, death_y, spawn_x, spawn_y, goal_x;
    const Surface *surfaces;
    unsigned surface_count;
} MovementLevel;
typedef struct {
    float x,y,vx,vy,height;
    unsigned deaths, respawn_ticks;
    int grounded, crouched, finished, on_slope;
} Player;
extern const MovementLevel movement_test_level;
void player_reset(Player *p, const MovementLevel *level);
/* Exactly one 60 Hz step. No allocations; swept axis collision against solids. */
void player_step(Player *p, const MovementLevel *level, const Actions *a);
float player_camera_x(const Player *p, const MovementLevel *level, float view_width);
#endif
