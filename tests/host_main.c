#include <stdio.h>
int run_core_tests(void);
int main(void) {
    int result=run_core_tests();
    if(result) { fprintf(stderr,"C core test failed at core_tests.c:%d\n",result); return 1; }
    puts("PASS portable C input/timing/visibility tests; not a native 3DS or gameplay test");
    return 0;
}
