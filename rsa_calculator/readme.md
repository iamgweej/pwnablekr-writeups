# rsa_calculator

This thing is **super** buggy.

Only a few of the primitives I've found:
A super weird overflow in `g_ebuf` (look at `RSA_encrypt+18B`)
A format string bug in `RSA_decrypt+28E`.
A weird stack buffer overflow `RSA_decrypt`

## Ideas

### Idea #1 

Exploiting the `g_ebuf` overflow: really hard, requires forging a special RSA key.

### Idea #2

Exploiting the format string:

* Use the format string to leak a stack address.
* Put my `execve("/bin/sh")` code on the stack.
* Override a function pointer in `funcs[]` to point to my shellcode.
* Victory.

### Idea #3

Exploiting the stack buffer overflow in `RSA_decrypt`:

* Use the format string bug to get the canary (and maybe get a stack pointer?).
* Overflow the buffer, keeping the canary, and redirecting execution to stack shellcode.
  * Maybe it would be easier to "push" `system()` arguments and redirect exection to `libc` `system()`?
* Victory.

Problems: 
* This overflow sucks ass and its really hard to control it (a bit like the `g_ebuf` overflow).
* `scanf` writes full length integers which fucks with my shellcode and `%n`.

### Idea #4
* Use the format string to get a stack leak.
* override `help()` to point to stack shellcode using format string.
* profit!

Problems:
* I cant seem to find a stack address anywhere! I sat on this for like 4 hours... 

### Idea #5

Make a usual function the program uses, of which we can control the input, and point it to `system()` using the write-what-where the format string gives us, by the means of overriding the `got`.

* Override `printf()` `got` entry, and make it point to `system()`.
* Call `printf()` with our `"/bin/sh"` input using `RSA_decrypt()`.
* Victory. 

As you can see by mt solution, this one actually worked!

## Stuff I noticed:

`"%12$x"` - the start of `hex_string`
`"%205$x"` - the `canary`.
`"%206$x"` - saved `rbp`.
`"%207$x"` - saved `rip`.

## Snippets

```python
def encode(b):
    return b''.join(binascii.hexlify(struct.pack("<I", c)) for c in b)
```

An idea I toyed with:

override `help()` (option 4) with an address.
encode(b"%43690x%32$n") + 64*b'A' + b'\x18\x25\x60'
encode(b"%43690x%32$n") + 64*b'A' + b'\x1a\x25\x60'
encode(b"%43690x%32$n") + 64*b'A' + b'\x1c\x25\x60'
encode(b"%43690x%32$n") + 64*b'A' + b'\x1e\x25\x60'

read the `got`:
encode(b"%22$s") + 40*b'A' + b'\x28\x20\x60'
