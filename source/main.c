/* Native development viewer. It does not implement NSMBW gameplay. */
#include <3ds.h>
#include <citro2d.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include "core.h"

static Scene scene;
static uint8_t file_bytes[SCENE_MAX_BYTES];
static float camera_x, camera_y;
static const float scale=0.625f; /* 640x360 inspection view -> 400x225 */
static char status[128];
typedef struct { float frame_ms, cpu_ms, gpu_ms; uint32_t visible, dropped; } Sample;
#define SAMPLE_CAPACITY 3600
static Sample samples[SAMPLE_CAPACITY];
static unsigned sample_count;

static uint32_t buttons_from_hid(uint32_t k) {
    uint32_t b=0;
    const uint32_t hardware[]={KEY_DLEFT,KEY_DRIGHT,KEY_DUP,KEY_DDOWN,KEY_A,KEY_B,
        KEY_X,KEY_Y,KEY_R,KEY_L,KEY_ZL,KEY_ZR,KEY_START};
    const uint32_t logical[]={BTN_LEFT,BTN_RIGHT,BTN_UP,BTN_DOWN,BTN_A,BTN_B,
        BTN_X,BTN_Y,BTN_R,BTN_L,BTN_ZL,BTN_ZR,BTN_START};
    for (unsigned i=0;i<sizeof(hardware)/sizeof(hardware[0]);i++) if(k&hardware[i]) b|=logical[i];
    return b;
}
static int load_area(unsigned area) {
    char path[128];
    snprintf(path,sizeof(path),"sdmc:/3ds/nsmbw-prototype/data/01-01-area%u.nsc",area);
    FILE *f=fopen(path,"rb");
    if(!f) { scene.count=0; snprintf(status,sizeof(status),"Missing area %u data on SD.",area); return 0; }
    size_t n=fread(file_bytes,1,sizeof(file_bytes),f);
    int extra=fgetc(f), error=ferror(f);
    fclose(f);
    if(error||extra!=EOF||!scene_decode(&scene,file_bytes,n)) {
        scene.count=0; snprintf(status,sizeof(status),"Area %u data invalid or unsupported.",area); return 0;
    }
    camera_x=(float)scene.start_x-160; camera_y=(float)scene.start_y-240;
    snprintf(status,sizeof(status),"Area %u: %lu placement records",area,(unsigned long)scene.count);
    return 1;
}
static float maxf(float a,float b) { return a>b?a:b; }
static float minf(float a,float b) { return a<b?a:b; }
static void clipped_rect(float x,float y,float w,float h,uint32_t color) {
    float left=maxf(x,0), top=maxf(y,7.5f), right=minf(x+w,400), bottom=minf(y+h,232.5f);
    if(right>left&&bottom>top) C2D_DrawRectSolid(left,top,0,right-left,bottom-top,color);
}
static void outline(float x,float y,float w,float h,uint32_t color) {
    clipped_rect(x,y,w,1,color); clipped_rect(x,y+h-1,w,1,color);
    clipped_rect(x,y,1,h,color); clipped_rect(x+w-1,y,1,h,color);
}
static unsigned draw_scene(void) {
    unsigned visible=0;
    uint32_t layer_colors[]={C2D_Color32(136,182,255,140),C2D_Color32(98,211,146,200),C2D_Color32(183,152,237,120)};
    for(uint32_t i=0;i<scene.count;i++) {
        const SceneRecord *r=&scene.records[i];
        if(!scene_visible(r,camera_x,camera_y,640,360)) continue;
        visible++;
        float x=(r->x-camera_x)*scale,y=7.5f+(r->y-camera_y)*scale;
        float w=r->w*scale,h=r->h*scale;
        if(r->kind==0) outline(x,y,w,h,layer_colors[r->layer]);
        else if(r->kind==1) clipped_rect(x,y,w,h,C2D_Color32(255,169,80,255));
        else if(r->kind==2) clipped_rect(x,y,w,h,C2D_Color32(103,233,241,255));
        else outline(x,y,w,h,C2D_Color32(255,255,255,255));
    }
    return visible;
}
static int save_samples(const FixedClock *clock) {
    char path[128];
    /* Exclusive create prevents accidental overwrite of an earlier capture. */
    snprintf(path,sizeof(path),"sdmc:/3ds/nsmbw-prototype/viewer-%llu.csv",(unsigned long long)osGetTime());
    FILE *f=fopen(path,"wx");
    if(!f) return 0;
    fprintf(f,"# viewer only; not game performance; static_buffers_bytes=%lu; clipped_seconds=%.3f\n",
            (unsigned long)(sizeof(scene)+sizeof(file_bytes)+sizeof(samples)),clock->clipped_seconds);
    fprintf(f,"frame,frame_ms,citro3d_cpu_ms,citro3d_gpu_ms,visible_records,total_discarded_steps\n");
    for(unsigned i=0;i<sample_count;i++) fprintf(f,"%u,%.5f,%.5f,%.5f,%lu,%lu\n",i,samples[i].frame_ms,
        samples[i].cpu_ms,samples[i].gpu_ms,(unsigned long)samples[i].visible,(unsigned long)samples[i].dropped);
    int failed=ferror(f);
    if(fclose(f)!=0) failed=1;
    return !failed;
}
int main(void) {
    gfxInitDefault(); gfxSet3D(false); consoleInit(GFX_BOTTOM,NULL);
    bool is_new=false;
    if(R_FAILED(APT_CheckNew3DS(&is_new))||!is_new) {
        printf("This development viewer targets\nNew Nintendo 3DS systems.\nPress START to exit.\n");
        while(aptMainLoop()) { hidScanInput(); if(hidKeysDown()&KEY_START) break; gspWaitForVBlank(); }
        gfxExit(); return 1;
    }
    osSetSpeedupEnable(true);
    if(!C3D_Init(C3D_DEFAULT_CMDBUF_SIZE)) { gfxExit(); return 1; }
    if(!C2D_Init(4096)) { C3D_Fini(); gfxExit(); return 1; }
    C2D_Prepare();
    C3D_RenderTarget *target=C2D_CreateScreenTarget(GFX_TOP,GFX_LEFT);
    if(!target) { C2D_Fini(); C3D_Fini(); gfxExit(); return 1; }
    load_area(1);
    InputState input={0}; FixedClock clock={0}; Actions actions={0};
    unsigned frames=0, shown=0, area=1; uint32_t pending=0;
    uint64_t last=svcGetSystemTick();
    while(aptMainLoop()) {
        uint64_t now=svcGetSystemTick();
        double elapsed=(double)(now-last)/(double)SYSCLOCK_ARM11; last=now;
        hidScanInput(); uint32_t held=hidKeysHeld(), down=hidKeysDown();
        if((held&(KEY_SELECT|KEY_START))==(KEY_SELECT|KEY_START)) break;
        if((down&KEY_SELECT)&&!(held&KEY_START)) { area=area==1?2:1; load_area(area); }
        circlePosition circle; hidCircleRead(&circle);
        pending|=buttons_from_hid(down);
        unsigned steps=clock_advance(&clock,elapsed);
        for(unsigned i=0;i<steps;i++) {
            actions=input_step(&input,buttons_from_hid(held)|pending,circle.dx,circle.dy,0);
            pending=0;
            if(!actions.paused) {
                float speed=actions.run_fire?8:4;
                camera_x+=actions.move_x*speed; camera_y+=actions.move_y*speed;
                camera_x=maxf(0,minf(camera_x,1048560)); camera_y=maxf(0,minf(camera_y,1048560));
            }
        }
        if(frames%15==0) {
            printf("\x1b[HNSMBW development viewer\n");
            printf("GEOMETRY ONLY - NO GAMEPLAY\n\n");
            printf("%-39s\n",status);
            printf("Move: D-pad / Circle Pad\nY: faster camera\nSELECT: change area\nSTART: pause\nSELECT+START: save log and exit\n\n");
            printf("Visible: %-5u / %-5lu\n",shown,(unsigned long)scene.count);
            printf("X/Y: %-9.1f %-9.1f\n",camera_x,camera_y);
            printf("Jump:%d X carry:%d R:%d Tilt:%2d\n",actions.jump_held,!!(held&KEY_X),!!(held&KEY_R),actions.tilt);
            printf("Paused: %d   Dropped: %-8lu\n",input.paused,(unsigned long)clock.discarded_steps);
            printf("Capture: %-4u / %u frames\n",sample_count,SAMPLE_CAPACITY);
        }
        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
        C2D_TargetClear(target,C2D_Color32(12,18,30,255)); C2D_SceneBegin(target);
        shown=draw_scene();
        C3D_FrameEnd(0);
        /* Timings belong to the viewer; the first frame has no prior timing. */
        if(frames&&sample_count<SAMPLE_CAPACITY) samples[sample_count++]=(Sample){(float)(elapsed*1000),
            C3D_GetProcessingTime(),C3D_GetDrawingTime(),shown,clock.discarded_steps};
        frames++;
    }
    if(!save_samples(&clock)) {
        printf("\nCould not save viewer timing log.\nPress B to exit.\n");
        while(aptMainLoop()) { hidScanInput(); if(hidKeysDown()&KEY_B) break; gspWaitForVBlank(); }
    }
    C2D_Fini(); C3D_Fini(); gfxExit(); return 0;
}
