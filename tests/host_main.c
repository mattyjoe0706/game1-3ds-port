#include <stdio.h>
int run_core_tests(void);
int run_movement_tests(void);
int run_terrain_tests(void);
int run_enemies_tests(void);
int main(void) {
    int result=run_core_tests();
    if(result) { fprintf(stderr,"C core test failed at core_tests.c:%d\n",result); return 1; }
    result=run_movement_tests();
    if(result) { fprintf(stderr,"Movement test failed at movement_tests.c:%d\n",result); return 1; }
    result=run_terrain_tests();
    if(result) { fprintf(stderr,"Terrain test failed at terrain_tests.c:%d\n",result); return 1; }
    result=run_enemies_tests();
    if(result) { fprintf(stderr,"Enemy test failed at enemies_tests.c:%d\n",result); return 1; }
    puts("PASS portable core, movement, terrain and enemy tests; not native 3DS validation");
    return 0;
}
