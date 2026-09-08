#ifndef NSMBW_CORE_H
#define NSMBW_CORE_H
#include <stdint.h>
#include <stddef.h>

#define SCENE_CAPACITY 4096
#define SCENE_HEADER_SIZE 32
#define SCENE_RECORD_SIZE 24
#define SCENE_MAX_BYTES (SCENE_HEADER_SIZE + SCENE_CAPACITY * SCENE_RECORD_SIZE)

typedef struct {
    uint8_t kind, layer;
    uint16_t id;
    int32_t x, y, w, h;
    uint32_t param;
} SceneRecord;
typedef struct {
    uint32_t area, count, start_x, start_y;
    SceneRecord records[SCENE_CAPACITY];
} Scene;
/* Fail closed: invalid input sets count to zero. No disk or heap access. */
int scene_decode(Scene *scene, const uint8_t *bytes, size_t length);
int scene_visible(const SceneRecord *record, float x, float y, float w, float h);

enum {
    BTN_LEFT=1u<<0, BTN_RIGHT=1u<<1, BTN_UP=1u<<2, BTN_DOWN=1u<<3,
    BTN_A=1u<<4, BTN_B=1u<<5, BTN_X=1u<<6, BTN_Y=1u<<7,
    BTN_R=1u<<8, BTN_L=1u<<9, BTN_ZL=1u<<10, BTN_ZR=1u<<11,
    BTN_START=1u<<12
};
typedef struct {
    uint32_t previous;
    int carrying, paused;
} InputState;
typedef struct {
    int move_x, move_y, jump_pressed, jump_held, run_fire;
    int pickup, throw_object, carry_held, spin, tilt, paused;
} Actions;
/* Call at 60 Hz. Eligibility comes from the future actor/collision system.
 * X pickup is edge-triggered; an unsuccessful press must be released to retry.
 * Object destruction/death must clear state.carrying in the caller.
 */
Actions input_step(InputState *state, uint32_t buttons, int pad_x, int pad_y, int can_pickup);

typedef struct { double pending, clipped_seconds; uint32_t discarded_steps; } FixedClock;
/* At most five updates/frame. Long stalls are accounted for, never hidden. */
unsigned clock_advance(FixedClock *clock, double elapsed_seconds);
#endif
