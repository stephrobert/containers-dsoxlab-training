#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    errno = 0;
    /* Match only the reserved probe argument, never runtime parent queries. */
    long result = syscall(SYS_getpgid, 2147483647UL);
    if (result == -1 && errno == EPERM
        && syscall(SYS_getpgid, 0UL) > 0 && syscall(SYS_getpid) > 0) {
        puts("getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed");
        return 0;
    }
    puts("filter-not-effective");
    return 1;
}
