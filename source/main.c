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
#include "terrain.h"
#include "enemies.h"
#include "character.h"
static CharacterAnim character;
static C3D_Tex character_texture;
static bool character_ready;
static uint32_t character_texture_hash;
static bool character_atlas_view;

static Scene scene;
static Terrain terrain;
static Enemies enemies;
static uint8_t enemy_bytes[ENEMY_MAX_BYTES];
static bool enemies_ready;
static uint32_t terrain_package_hash;
static uint8_t terrain_bytes[TERRAIN_MAX_BYTES];
static C3D_Tex terrain_texture;
static bool terrain_ready;


static uint8_t file_bytes[SCENE_MAX_BYTES];
static float camera_x, camera_y;
static const float scale=0.625f; /* 640x360 inspection view -> 400x225 */
static char status[128];
typedef struct { float frame_ms, cpu_ms, gpu_ms; uint32_t visible, dropped, mode, atlas_view; } Sample;
#define SAMPLE_CAPACITY 3600
static Sample samples[SAMPLE_CAPACITY];
static unsigned sample_count;
static Player player;
static unsigned mode; /* 0: authored; 1/2: placements; 3: real terrain slice */
static const MovementLevel *active_level(void) {
    return mode==3?&terrain.level:&movement_test_level;
}
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
static int load_terrain(void) {
    FILE *f=fopen("sdmc:/3ds/nsmbw-prototype/data/terrain.nst","rb");
    if(!f) { snprintf(status,sizeof(status),"Terrain data missing (errno %d)",errno); return 0; }
    size_t n=fread(terrain_bytes,1,sizeof(terrain_bytes),f);
    int extra=fgetc(f),error=ferror(f); fclose(f);
    if(error||extra!=EOF||!terrain_decode(&terrain,terrain_bytes,n)) {
        snprintf(status,sizeof(status),"Terrain package invalid or incompatible"); return 0;
    }
    terrain_package_hash=terrain_hash(terrain_bytes,n);
    if(!C3D_TexInit(&terrain_texture,512,512,GPU_RGBA8)) {
        snprintf(status,sizeof(status),"Terrain texture allocation failed"); return 0;
    }
    f=fopen("sdmc:/3ds/nsmbw-prototype/data/terrain.rgba","rb");
    if(!f) {
        C3D_TexDelete(&terrain_texture);
        snprintf(status,sizeof(status),"Terrain texture missing (errno %d)",errno); return 0;
    }
    n=fread(terrain_texture.data,1,TERRAIN_TEXTURE_BYTES,f);
    extra=fgetc(f); error=ferror(f); fclose(f);
    if(error||extra!=EOF||n!=TERRAIN_TEXTURE_BYTES||
       terrain_hash(terrain_texture.data,n)!=terrain.texture_hash) {
        C3D_TexDelete(&terrain_texture);
        snprintf(status,sizeof(status),"Terrain texture size/checksum mismatch"); return 0;
    }
    C3D_TexSetFilter(&terrain_texture,GPU_NEAREST,GPU_NEAREST);
    C3D_TexSetWrap(&terrain_texture,GPU_CLAMP_TO_EDGE,GPU_CLAMP_TO_EDGE);
    C3D_TexFlush(&terrain_texture);
    terrain_ready=true;
    snprintf(status,sizeof(status),"Terrain ready: %lu tiles",(unsigned long)terrain.count);
    return 1;
}
static void load_enemies(void) {
    FILE *f=fopen("sdmc:/3ds/nsmbw-prototype/data/enemies.nse","rb");
    if(!f) { checkpoint("Enemy data missing; terrain-only mode"); return; }
    size_t n=fread(enemy_bytes,1,sizeof(enemy_bytes),f);
    int extra=fgetc(f),error=ferror(f); fclose(f);
    if(error||extra!=EOF||!enemies_decode(&enemies,enemy_bytes,n,terrain_package_hash,&terrain.level)) {
        checkpoint("Enemy data invalid/mismatched; terrain-only mode"); return;
    }
    enemies_ready=true;
    checkpoint("ENEMY TEST 1: Goomba placements loaded");
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
static void load_character(void) {
    uint8_t header[32]; uint32_t hash;
    FILE *f=fopen("sdmc:/3ds/nsmbw-prototype/data/mario.nsp","rb");
    if(!f) { checkpoint("Mario package missing; yellow player fallback"); return; }
    size_t n=fread(header,1,sizeof(header),f);int extra=fgetc(f),error=ferror(f);fclose(f);
    if(error||extra!=EOF||!character_header(header,n,&hash)) { checkpoint("Mario header invalid; yellow fallback"); return; }
    if(!C3D_TexInit(&character_texture,512,256,GPU_RGBA8)) { checkpoint("Mario texture allocation failed; yellow fallback"); return; }
    f=fopen("sdmc:/3ds/nsmbw-prototype/data/mario.rgba","rb");
    if(!f) { C3D_TexDelete(&character_texture);checkpoint("Mario texture missing; yellow fallback");return; }
    n=fread(character_texture.data,1,CHARACTER_TEXTURE_BYTES,f);extra=fgetc(f);error=ferror(f);fclose(f);
    if(error||extra!=EOF||n!=CHARACTER_TEXTURE_BYTES||terrain_hash(character_texture.data,n)!=hash) {
        C3D_TexDelete(&character_texture);checkpoint("Mario texture checksum/size invalid; yellow fallback");return;
    }
    C3D_TexSetFilter(&character_texture,GPU_NEAREST,GPU_NEAREST);
    C3D_TexSetWrap(&character_texture,GPU_CLAMP_TO_EDGE,GPU_CLAMP_TO_EDGE);
    C3D_TexFlush(&character_texture);character_ready=true;character_texture_hash=hash;
    char message[96];
    snprintf(message,sizeof(message),"SPRITE DIAGNOSTIC 2: loaded texture %08lX",(unsigned long)hash);
    checkpoint(message);
}
static void draw_character_atlas(void) {
    /* Whole sheet uses fixed UVs, independently of animation-cell selection. */
    Tex3DS_SubTexture sub={.width=512,.height=256,.left=0,.top=1,.right=1,.bottom=0};
    C2D_Image image={&character_texture,&sub};
    C2D_DrawRectSolid(0,0,0,400,240,C2D_Color32(35,45,60,255));
    C2D_DrawImageAt(image,8,16,0,NULL,0.75f,0.75f);
    for(unsigned row=0;row<4;row++) for(unsigned col=0;col<8;col++)
        outline(8+col*48,16+row*48,48,48,C2D_Color32(90,100,110,255));
    unsigned frame=character_frame(&character);
    outline(8+(frame%8)*48,16+(frame/8)*48,48,48,C2D_Color32(255,220,0,255));
}
static void draw_player(void) {
    if(player.respawn_ticks) return;
    if(!character_ready) {
        clipped_rect((player.x-camera_x)*scale,7.5f+(player.y-camera_y)*scale,16*scale,player.height*scale,C2D_Color32(255,205,80,255));return;
    }
    unsigned frame=character_frame(&character);
    float u=(frame%8)/8.0f,v=1.0f-(frame/8)/4.0f;
    Tex3DS_SubTexture sub={.width=64,.height=64,.left=u,.top=v,.right=u+1/8.0f,.bottom=v-1/4.0f};
    if(character.facing<0) { sub.left=u+1/8.0f;sub.right=u; }
    C2D_Image image={&character_texture,&sub};
    float height=player.crouched?24.0f:48.0f;
    C2D_DrawImageAt(image,(player.x+8-24-camera_x)*scale,
        7.5f+(player.y+player.height-height*(15/16.0f)-camera_y)*scale,0,NULL,48*scale/64,height*scale/64);
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
    draw_player();
    return visible;
}
static void draw_enemies(void) {
    for(unsigned i=0;i<enemies.count;i++) {
        const Enemy *e=&enemies.items[i];
        if(e->state!=1&&e->state!=2) continue;
        float x=(e->body.x-camera_x)*scale,y=7.5f+(e->body.y-camera_y)*scale;
        if(x+16*scale<0||x>400) continue;
        uint32_t brown=C2D_Color32(145,80,35,255),dark=C2D_Color32(67,35,20,255);
        if(e->state==2) { clipped_rect(x,y+12*scale,16*scale,4*scale,brown); continue; }
        clipped_rect(x+2*scale,y,12*scale,5*scale,brown);
        clipped_rect(x,y+5*scale,16*scale,7*scale,brown);
        clipped_rect(x+3*scale,y+11*scale,10*scale,3*scale,C2D_Color32(224,188,128,255));
        clipped_rect(x,y+14*scale,6*scale,2*scale,dark);
        clipped_rect(x+10*scale,y+14*scale,6*scale,2*scale,dark);
        clipped_rect(x+3*scale,y+5*scale,3*scale,4*scale,C2D_Color32(255,255,255,255));
        clipped_rect(x+10*scale,y+5*scale,3*scale,4*scale,C2D_Color32(255,255,255,255));
        clipped_rect(x+4*scale,y+6*scale,scale,2*scale,dark);
        clipped_rect(x+11*scale,y+6*scale,scale,2*scale,dark);
    }
}
static unsigned draw_terrain(void) {
    unsigned visible=0;
    clipped_rect(0,7.5f,400,225,C2D_Color32(91,160,208,255));
    for(unsigned i=0;i<terrain.count;i++) {
        const TerrainTile *t=&terrain.tiles[i];
        if(t->x+16<=camera_x||t->x>=camera_x+640||t->y+16<=camera_y||t->y>=camera_y+360) continue;
        float u=(t->tile%32)*16/512.0f,v=1.0f-(t->tile/32)*16/512.0f;
        Tex3DS_SubTexture sub={.width=16,.height=16,.left=u,.top=v,.right=u+16/512.0f,.bottom=v-16/512.0f};
        C2D_Image image={&terrain_texture,&sub};
        C2D_DrawImageAt(image,(t->x-camera_x)*scale,7.5f+(t->y-camera_y)*scale,0,NULL,scale,scale);
        visible++;
    }
    draw_enemies();
    clipped_rect((terrain.level.goal_x-camera_x)*scale,7.5f,2,225,C2D_Color32(93,240,120,255));
    draw_player();
    /* Preserve the 640x360 proportional viewport, including at vertical edges. */
    C2D_DrawRectSolid(0,0,0,400,7.5f,C2D_Color32(12,18,30,255));
    C2D_DrawRectSolid(0,232.5f,0,400,7.5f,C2D_Color32(12,18,30,255));
    return visible;
}
static int save_samples(const FixedClock *clock) {
    char path[128];
    /* Exclusive create prevents accidental overwrite of an earlier capture. */
    snprintf(path,sizeof(path),"sdmc:/3ds/nsmbw-prototype/viewer-%llu.csv",(unsigned long long)osGetTime());
    FILE *f=fopen(path,"wx");
    if(!f) return 0;
    fprintf(f,"# movement test/placement viewer; not Wii gameplay; static_buffers_bytes=%lu; clipped_seconds=%.3f\n",
            (unsigned long)(sizeof(scene)+sizeof(file_bytes)+sizeof(samples)+sizeof(player)+sizeof(terrain)+sizeof(terrain_bytes)+sizeof(enemies)+sizeof(enemy_bytes)+sizeof(character)),clock->clipped_seconds);
    fprintf(f,"# terrain_texture_bytes=%u; mode3=terrain_slice; timings_not_full_game\n",(unsigned)(terrain_ready?TERRAIN_TEXTURE_BYTES:0));
    fprintf(f,"# enemy_test=1; enemies_loaded=%u; pause_not_logged\n",enemies_ready?enemies.count:0);
    fprintf(f,"# mario_sprite_test=1; mario_loaded=%u; mario_texture_bytes=%u\n",character_ready?1u:0u,character_ready?CHARACTER_TEXTURE_BYTES:0u);
    fprintf(f,"# sprite_diagnostic=2; mario_texture_fnv=%08lX\n",(unsigned long)character_texture_hash);
    fprintf(f,"frame,frame_ms,citro3d_cpu_ms,citro3d_gpu_ms,visible_records,total_discarded_steps,mode,atlas_view\n");
    for(unsigned i=0;i<sample_count;i++) fprintf(f,"%u,%.5f,%.5f,%.5f,%lu,%lu,%lu,%lu\n",i,samples[i].frame_ms,
        samples[i].cpu_ms,samples[i].gpu_ms,(unsigned long)samples[i].visible,(unsigned long)samples[i].dropped,(unsigned long)samples[i].mode,(unsigned long)samples[i].atlas_view);
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
    checkpoint("[10] Loading TERRAIN TEST 1 package");
    if(load_terrain()) mode=3;
    checkpoint(status);
    if(terrain_ready) load_enemies();
    load_character();character_reset(&character);
    if(!terrain_ready) checkpoint("Using authored course. Add terrain.nst + terrain.rgba, then relaunch.");
    player_reset(&player,active_level()); enemies_reset(&enemies); character_reset(&character);
    camera_x=player_camera_x(&player,active_level(),640); camera_y=mode==3?-40:160;
    checkpoint("TERRAIN TEST 1 - opening slice, approximate physics");
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
        if((down&KEY_R)&&character_ready&&(mode==0||mode==3)) character_atlas_view=!character_atlas_view;
        if((down&KEY_SELECT)&&!(held&KEY_START)) {
            mode=(mode+1)%4;
            character_atlas_view=false;
            if(mode==3&&!terrain_ready) mode=0;
            input=(InputState){0}; pending=0;
            if(mode==1||mode==2) load_area(mode);
            else { player_reset(&player,active_level()); enemies_reset(&enemies); character_reset(&character); camera_x=player_camera_x(&player,active_level(),640); camera_y=mode==3?-40:160; }
        }
        if((mode==0||mode==3)&&(down&KEY_TOUCH)) {
            player_reset(&player,active_level()); enemies_reset(&enemies); character_reset(&character);
            input=(InputState){0}; pending=0;
        }
        circlePosition circle; hidCircleRead(&circle);
        pending|=buttons_from_hid(down);
        unsigned steps=clock_advance(&clock,elapsed);
        for(unsigned i=0;i<steps;i++) {
            actions=input_step(&input,buttons_from_hid(held)|pending,circle.dx,circle.dy,0);
            pending=0;
            if(character_atlas_view) actions.paused=1;
            if(mode==0||mode==3) {
                if(mode==3&&enemies_ready) encounter_step(&enemies,&player,active_level(),&actions,camera_x);
                else player_step(&player,active_level(),&actions);
                character_step(&character,player.vx,player.grounded,player.crouched,actions.paused,player.respawn_ticks!=0);
                camera_x=player_camera_x(&player,active_level(),640); camera_y=mode==3?-40:160;
            } else if(!actions.paused) {
                float speed=actions.run_fire?8:4;
                camera_x+=actions.move_x*speed; camera_y+=actions.move_y*speed;
                camera_x=maxf(0,minf(camera_x,1048560)); camera_y=maxf(0,minf(camera_y,1048560));
            }
        }
        if(frames&&frames%15==0) {
            consoleClear();
            if(mode==0||mode==3) {
                printf("%s\n\n",mode==3?(enemies_ready?"ENEMY TEST 1 - World 1-1 opening\nTemporary enemies; no audio":"ENEMY TEST 1 - terrain only\nEnemy data not loaded"):"MOVEMENT TEST 1 - Authored course");
                printf("D-pad / Circle Pad: move\nA / B: jump (hold for height)\nY: run   Down: crouch\nTouch screen: restart\n");
                printf("SPRITE DIAGNOSTIC 2: %s\n",character_ready?"loaded":"yellow fallback");
                printf("Texture: %08lX  Frame: %u\n",(unsigned long)character_texture_hash,character_frame(&character));
                printf("R: sheet view %s\n",character_atlas_view?"ON (game frozen)":"OFF");
                if(mode==3&&enemies_ready) printf("Goombas: %u  Stomps: %u\n",enemies.count,enemies.stomps);
                printf("Player: %.1f, %.1f\nDeaths: %u  Grounded: %d\n",player.x,player.y,player.deaths,player.grounded);
                printf("%s\n",player.finished?"FINISHED! Touch to restart":(player.respawn_ticks?"Fell! Restarting...":"Reach the green section marker"));
            } else {
                printf("WORLD 1-1 PLACEMENT INSPECTOR\nOutlines only - no player collision\n\n%s\n",status);
                printf("D-pad: camera   Y: faster\nVisible: %u / %lu\n",shown,(unsigned long)scene.count);
            }
            printf("\nSELECT: test / areas / terrain\nSTART: pause\nSELECT+START: save and exit\n");
            printf("Paused: %d   Dropped: %-8lu\n",input.paused,(unsigned long)clock.discarded_steps);
            printf("Capture: %-4u / %u frames\n",sample_count,SAMPLE_CAPACITY);
            gfxFlushBuffers();
        }
        if(!frames) checkpoint("[12] Entering first C3D_FrameBegin");
        if(!C3D_FrameBegin(C3D_FRAME_SYNCDRAW)) {
            diagnostic_error("ERROR: C3D_FrameBegin failed"); goto cleanup;
        }
        C2D_TargetClear(target,C2D_Color32(12,18,30,255)); C2D_SceneBegin(target);
        shown=mode==3?draw_terrain():(mode?draw_scene():draw_movement());
        if(character_atlas_view) draw_character_atlas();
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
            C3D_GetProcessingTime(),C3D_GetDrawingTime(),shown,clock.discarded_steps,mode,character_atlas_view?1u:0u};
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
    if(c3d_ready) C3D_FrameSync();
    if(terrain_ready) C3D_TexDelete(&terrain_texture);
    if(character_ready) C3D_TexDelete(&character_texture);
    if(c2d_ready) C2D_Fini();
    if(c3d_ready) C3D_Fini();
    checkpoint("[18] Returning to launcher");
    diagnostic_console=false;
    gfxExit(); return exit_code;
}
