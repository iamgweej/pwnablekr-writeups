#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char const *argv[])
{
    srand(time(NULL));

    if(argc < 2) {
        return 1;
    }

    int captcha = atoi(argv[1]);
    int canary;
    int arr[8];

    for(int i = 0; i < 8; ++i) {
        arr[i] = rand();
    }

    canary = captcha;
    canary -= (arr[1] + arr[5]);
    canary -= (arr[2] - arr[3]);
    canary -= arr[7];
    canary -= (arr[4] - arr[6]);

    printf("%x\n", canary);
    return 0;
}

