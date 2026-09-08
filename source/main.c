/* Authored movement test and Wii placement viewer; not faithful NSMBW gameplay. */
#include <3ds.h>
#include <citro2d.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <errno.h>
#include <sys/stat.h>
#include "core.h"
#include "movement.h"

static Scene scene;
static uint8_t file_bytes[SCENE_MAX_BYTES];
static float camera_x, camera_y;
static const float scale=0.625f; /* 640x360 inspection view -> 400x225 */
static char status[128];
typedef struct { float frame_ms, cpu_ms, gpu_ms; uint32_t visible, dropped, mode; } Sample;
#define SAMPLE_CAPACITY 3600
static Sample samples[SAMPLE_CAPACITY];
static unsigned sample_count;
static Player player;
static unsigned mode; /* 0: authored course; 1/2: Wii placement inspector */
static bool diagnostic_console;
static int startup_log_error;
#define STARTUP_LOG "sdmc:/nsmbw-startup.log"

/* Append and close every checkpoint so a later hang cannot hold it in stdio.
 * The SD root works even if the application's data directory is missing. */
static void checkpoint(const char *message) {
    if(diagnostic_console) {
        printf("%s\n",message);
        fflush(stdout);
        gfxFlushBuffers();
    }
    if(!startup_log_error) {
        FILE *f=fopen(STARTUP_LOG,"a");
        if(!f) startup_log_error=errno?errno:EIO;
        else {
            if(fprintf(f,"%s\n",message)<0) startup_log_error=errno?errno:EIO;
            if(fclose(f)!=0) startup_log_error=errno?errno:EIO;
        }
        if(startup_log_error&&diagnostic_console) {
            printf("SD startup log unavailable: errno %d\n",startup_log_error);
            fflush(stdout); gfxFlushBuffers();
        }
    }
}

static void diagnostic_error(const char *message) {
    checkpoint(message);
    checkpoint("Press B to return to the launcher.");
    /* Require a new press, not a key still held from the previous screen. */
    while(aptMainLoop()) {
        hidScanInput();
        if(hidKeysDown()&KEY_B) break;
        gspWaitForVBlank();
    }
}

static bool diagnostic_continue(void) {
    checkpoint("A: continue startup   B: exit");
    while(aptMainLoop()) {
        hidScanInput();
        if(hidKeysDown()&KEY_B) return false;
        if(hidKeysDown()&KEY_A) return true;
        gspWaitForVBlank();
    }
    return false;
}

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
    if(!f) { int e=errno; scene.count=0; snprintf(status,sizeof(status),"Area %u open failed: errno %d",area,e); return 0; }
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
static unsigned draw_movement(void) {
    unsigned visible=0;
    for(unsigned i=0;i<movement_test_level.count;i++) {
        const Solid *s=&movement_test_level.solids[i];
        if(s->x+s->w<=camera_x||s->x>=camera_x+640) continue;
        visible++;
        clipped_rect((s->x-camera_x)*scale,7.5f+(s->y-camera_y)*scale,
                     s->w*scale,s->h*scale,C2D_Color32(63,117,159,255));
    }
    clipped_rect((movement_test_level.goal_x-camera_x)*scale,7.5f+(320-camera_y)*scale,
                 4,128*scale,C2D_Color32(93,240,120,255));
    if(!player.respawn_ticks) {
        clipped_rect((player.x-camera_x)*scale,7.5f+(player.y-camera_y)*scale,
                     16*scale,player.height*scale,C2D_Color32(255,205,80,255));
    }
    return visible;
}
static int save_samples(const FixedClock *clock) {
    char path[128];
    /* Exclusive create prevents accidental overwrite of an earlier capture. */
    snprintf(path,sizeof(path),"sdmc:/3ds/nsmbw-prototype/viewer-%llu.csv",(unsigned long long)osGetTime());
    FILE *f=fopen(path,"wx");
    if(!f) return 0;
    fprintf(f,"# movement test/placement viewer; not Wii gameplay; static_buffers_bytes=%lu; clipped_seconds=%.3f\n",
            (unsigned long)(sizeof(scene)+sizeof(file_bytes)+sizeof(samples)+sizeof(player)),clock->clipped_seconds);
    fprintf(f,"frame,frame_ms,citro3d_cpu_ms,citro3d_gpu_ms,visible_records,total_discarded_steps,mode\n");
    for(unsigned i=0;i<sample_count;i++) fprintf(f,"%u,%.5f,%.5f,%.5f,%lu,%lu,%lu\n",i,samples[i].frame_ms,
        samples[i].cpu_ms,samples[i].gpu_ms,(unsigned long)samples[i].visible,(unsigned long)samples[i].dropped,(unsigned long)samples[i].mode);
    int failed=ferror(f);
    if(fclose(f)!=0) failed=1;
    return !failed;
}
int main(void) {
    char message[128];
    bool c3d_ready=false, c2d_ready=false;
    int exit_code=1;
    snprintf(message,sizeof(message),"\nSTARTUP DIAGNOSTIC 1: %llu",(unsigned long long)osGetTime());
    checkpoint(message);
    checkpoint("[00] Enter main; starting gfxInitDefault");
    gfxInitDefault();
    checkpoint("[01] Graphics ready; starting console");
    gfxSet3D(false);
    if(!consoleInit(GFX_BOTTOM,NULL)) {
        checkpoint("ERROR: consoleInit returned NULL");
        gfxExit(); return 1;
    }
    diagnostic_console=true;
    setvbuf(stdout,NULL,_IONBF,0);
    checkpoint("STARTUP DIAGNOSTIC 1");
    checkpoint("[02] Bottom console ready");
    if(startup_log_error) {
        snprintf(message,sizeof(message),"Startup log failed: errno %d",startup_log_error);
        checkpoint(message);
    }
    checkpoint("Log: SD root /nsmbw-startup.log");
    if(!diagnostic_continue()) { exit_code=0; goto cleanup; }
    checkpoint("[03] Checking New 3DS model");
    bool is_new=false;
    Result model_result=APT_CheckNew3DS(&is_new);
    if(R_FAILED(model_result)) {
        snprintf(message,sizeof(message),"ERROR: model query 0x%08lX",(unsigned long)(uint32_t)model_result);
        diagnostic_error(message); goto cleanup;
    }
    if(!is_new) { diagnostic_error("ERROR: New 3DS system required"); goto cleanup; }
    checkpoint("[04] Model OK; enabling speedup");
    osSetSpeedupEnable(true);
    checkpoint("[05] Speedup set; starting citro3d");
    if(!C3D_Init(C3D_DEFAULT_CMDBUF_SIZE)) { diagnostic_error("ERROR: C3D_Init failed"); goto cleanup; }
    c3d_ready=true;
    checkpoint("[06] Citro3d ready; starting citro2d");
    if(!C2D_Init(4096)) { diagnostic_error("ERROR: C2D_Init failed"); goto cleanup; }
    c2d_ready=true;
    checkpoint("[07] Citro2d ready; preparing renderer");
    C2D_Prepare();
    checkpoint("[08] Creating top screen target");
    C3D_RenderTarget *target=C2D_CreateScreenTarget(GFX_TOP,GFX_LEFT);
    if(!target) { diagnostic_error("ERROR: screen target creation failed"); goto cleanup; }
    checkpoint("[09] Target ready; checking SD folders");
    const char *folders[]={"sdmc:/3ds","sdmc:/3ds/nsmbw-prototype"};
    for(unsigned i=0;i<sizeof(folders)/sizeof(folders[0]);i++) {
        if(mkdir(folders[i],0777)!=0&&errno!=EEXIST) {
            snprintf(message,sizeof(message),"ERROR: mkdir failed: errno %d",errno);
            diagnostic_error(message); goto cleanup;
        }
    }
    checkpoint("[10] Starting authored movement course");
    player_reset(&player,&movement_test_level);
    camera_x=0; camera_y=160;
    checkpoint("Movement test 1 - NOT World 1-1");
    checkpoint("[11] Course ready; preparing first frame");
    if(!diagnostic_continue()) { exit_code=0; goto cleanup; }
    InputState input={0}; FixedClock clock={0}; Actions actions={0};
    unsigned frames=0, shown=0; uint32_t pending=0;
    uint64_t last=svcGetSystemTick();
    while(aptMainLoop()) {
        uint64_t now=svcGetSystemTick();
        double elapsed=(double)(now-last)/(double)SYSCLOCK_ARM11; last=now;
        hidScanInput(); uint32_t held=hidKeysHeld(), down=hidKeysDown();
        if((held&(KEY_SELECT|KEY_START))==(KEY_SELECT|KEY_START)) break;
        if((down&KEY_SELECT)&&!(held&KEY_START)) {
            mode=(mode+1)%3;
            input=(InputState){0}; pending=0;
            if(mode) load_area(mode);
            else { camera_x=player_camera_x(&player,&movement_test_level,640); camera_y=160; }
        }
        if(!mode&&(down&KEY_TOUCH)) {
            player_reset(&player,&movement_test_level);
            input=(InputState){0}; pending=0;
        }
        circlePosition circle; hidCircleRead(&circle);
        pending|=buttons_from_hid(down);
        unsigned steps=clock_advance(&clock,elapsed);
        for(unsigned i=0;i<steps;i++) {
            actions=input_step(&input,buttons_from_hid(held)|pending,circle.dx,circle.dy,0);
            pending=0;
            if(!mode) {
                player_step(&player,&movement_test_level,&actions);
                camera_x=player_camera_x(&player,&movement_test_level,640); camera_y=160;
            } else if(!actions.paused) {
                float speed=actions.run_fire?8:4;
                camera_x+=actions.move_x*speed; camera_y+=actions.move_y*speed;
                camera_x=maxf(0,minf(camera_x,1048560)); camera_y=maxf(0,minf(camera_y,1048560));
            }
        }
        if(frames&&frames%15==0) {
            consoleClear();
            if(!mode) {
                printf("MOVEMENT TEST 1\nAuthored course - not World 1-1\n\n");
                printf("D-pad / Circle Pad: move\nA / B: jump (hold for height)\nY: run   Down: crouch\nTouch screen: restart\n");
                printf("Player: %.1f, %.1f\nDeaths: %u  Grounded: %d\n",player.x,player.y,player.deaths,player.grounded);
                printf("%s\n",player.finished?"FINISHED! Touch to restart":(player.respawn_ticks?"Fell! Restarting...":"Reach the green finish pole"));
            } else {
                printf("WORLD 1-1 PLACEMENT INSPECTOR\nOutlines only - no player collision\n\n%s\n",status);
                printf("D-pad: camera   Y: faster\nVisible: %u / %lu\n",shown,(unsigned long)scene.count);
            }
            printf("\nSELECT: test / area 1 / area 2\nSTART: pause\nSELECT+START: save and exit\n");
            printf("Paused: %d   Dropped: %-8lu\n",input.paused,(unsigned long)clock.discarded_steps);
            printf("Capture: %-4u / %u frames\n",sample_count,SAMPLE_CAPACITY);
            gfxFlushBuffers();
        }
        if(!frames) checkpoint("[12] Entering first C3D_FrameBegin");
        if(!C3D_FrameBegin(C3D_FRAME_SYNCDRAW)) {
            diagnostic_error("ERROR: C3D_FrameBegin failed"); goto cleanup;
        }
        C2D_TargetClear(target,C2D_Color32(12,18,30,255)); C2D_SceneBegin(target);
        shown=mode?draw_scene():draw_movement();
        C3D_FrameEnd(0);
        if(!frames) {
            checkpoint("[13] First frame submitted; syncing GPU");
            C3D_FrameSync();
            checkpoint("[14] First frame synced; viewer running");
            /* Exclude diagnostic disk I/O from the next frame interval. */
            last=svcGetSystemTick();
        }
        /* Timings belong to the viewer; the first frame has no prior timing. */
        if(frames&&sample_count<SAMPLE_CAPACITY) samples[sample_count++]=(Sample){(float)(elapsed*1000),
            C3D_GetProcessingTime(),C3D_GetDrawingTime(),shown,clock.discarded_steps,mode};
        frames++;
    }
    checkpoint("[15] Leaving viewer; saving timing CSV");
    if(!save_samples(&clock)) {
        snprintf(message,sizeof(message),"ERROR: CSV save failed: errno %d",errno);
        diagnostic_error(message);
    } else {
        checkpoint("[16] Timing CSV saved");
        exit_code=0;
    }
cleanup:
    checkpoint("[17] Releasing graphics resources");
    if(c2d_ready) C2D_Fini();
    if(c3d_ready) C3D_Fini();
    checkpoint("[18] Returning to launcher");
    diagnostic_console=false;
    gfxExit(); return exit_code;
}
