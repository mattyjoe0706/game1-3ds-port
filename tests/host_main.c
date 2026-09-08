#include <stdio.h>
int run_core_tests(void);
int run_movement_tests(void);
int main(void) {
    int result=run_core_tests();
    if(result) { fprintf(stderr,"C core test failed at core_tests.c:%d\n",result); return 1; }
    result=run_movement_tests();
    if(result) { fprintf(stderr,"Movement test failed at movement_tests.c:%d\n",result); return 1; }
    puts("PASS portable core and authored movement tests; not native 3DS validation");
    return 0;
}
