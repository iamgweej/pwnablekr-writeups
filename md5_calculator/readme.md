#  MD5 Calculator

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
