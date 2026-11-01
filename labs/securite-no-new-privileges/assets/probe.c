#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("%lu:%lu\n", (unsigned long)getuid(), (unsigned long)geteuid());
    return 0;
}
