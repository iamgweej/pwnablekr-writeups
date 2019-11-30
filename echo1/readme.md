# echo1

Running the program, I see there is the option `BOF echo`, which is the only one provided. Looks promising.

Looking for something interesting, we see that `get_input()` tries to read 128 bytes into an area that can only hold 32 bytes. Looks promising.

Shoving `'A'*128` we get a `SIGSEGV`, as expected. Playing around with it in `gdb`, I see we can override the saved `rip` of `echo1()` with an offset of 40 bytes.

Now, here I tried several stuff:

* Not wanting to rely on the structure of the stack, I tried to jump to data that was allocated on the heap - namely the name I supplied the program. But then I've encoutered a bigger problem - `get_input()` uses `fgets()`, and **doesnt clear the trailing `'\n'`** ~~and stops on nullbytes~~. That means that what ever address we try to put there, there will be a trailing `\x0a` afterwards. Well, this is a big problem. Lets see what else can we find.
  * **Note**: Afterwards Iv'e found out that wasnt the case, and that `fgets` doesnt stop upon reading a nullbyte, only when reading a `\x0a` byte. Im keeping this in these notes since I've spent quite some time battelnig with this and it made me come up with a few ideas that might actually be usful!
* I checked the data segment my name is also stored on, just to see its not executable.
* I looked at the `got` addresses, maybe so I can get a valid address for my overflow in `echo1()`.
* Looked at `libc` functions addresses.

Hmm... what to do? I see a double free in `main()` (theres a flow for getting `cleanup()` called twice) but I dont see how that helps me since I dont see how to change `cs:o` after the first free.

I did fool around with the following idea: I searched for an interesting address in the code segment that has an `\x0a` character in it which might be usful. I've found a jump to a `scanf` thats scans into the stack (an offset defined by `rbp`) at `0x040a6c`, and since I control `rbp` I could maybe make it write everywhere I want. I forgot the null-termination after the `\x0a` that `fgets()` does, which pretty much trashed everything I've found. Not to mention that's already the address I'm returning too!

Well, I done goofed this time. Apparently, `<<< $()` is actually the one fucking with my null bytes! 

```text
/bin/bash: warning: command substitution: ignored null byte in input
```

When I try my payload with `<()`, `fgets()` takes my my nullbytes like a boss. Good to know. Will never fall for that one again!

This actually makes things a lot easier. I can actually put whatever address I want, so I can rely on the heap always allocating the place to store my name in the same address and jump to it (With a small 22 bytes `/bin/sh` shellcode I found online).

But theres actually a better solution! You can put the shellcode on the stack, point `rip` to `id` (which is stored at `0x6020a0`), and put a `jmp rsp` instruction in `id`, which will point the execution to our shellcode.

The flow will be a bit like this:

* In the `get_input()` stack frame:
  * We overflow the `fgets()` parameter, which will override the stored `rip` of the `echo1()` frame to `id`.
  * Afterwards, we put our `/bin/sh` shellcode.
* In the `echo1()` frame:
  * When the function `retn`'s, `rip` will be set to `id`, and `rsp` will point to our shellcode.
* The `jmp rsp` instruction stored in `id` is executed, which jumps to our shellcode.
* Victory!
