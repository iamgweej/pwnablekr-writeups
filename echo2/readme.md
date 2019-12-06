# Echo 2

First of all, we can guess that the global `o` is actually a struct:

```c
// Structure of global `o`
// sizeof(NameStruct) == 0x28
// Allocated on the heap
struct NameStruct {
    char name[24];
    void (*greet)(char *s);
    void (*bye)(char *s);
}
```

and that `cleanup()` is called before we stop using `o`, so we can get a classic use-after-free when we call `greet()` and `bye()`.

My initial idea:

* Put `name` to be 21 bytes long `/bin/sh` shellcode.
* enter `2` for stack info leak.
* calculate offset to `name` saved on the stack. (`"%llx"` in format string + 0x40).
* enter `4` to exit
* `o` is `free`'d
* enter `n` to cancel
* enter `3` and override the saved `greet()` function pointer saved in `o`, and point to `name` on the stack.
* Victory.

That worked on my machine, but it didnt seem to work on the pwnable.kr machine, which is strange.

Before doing more digging into getting another info leak, I noticed that the first argument to `greet()` and `bye()`, passed to them in `rdi`, is actually a pointer to a buffer we control, that is, `o->name`. If I find a `jmp rdi` or `call rdi` gadget in the code section I win.

When I began looking for this gadget, it occured to me that I could just put it somewhere myself: the first `qword` of my initial name is put into `id`, a global variable, so I can just set it to the opcodes of `jmp edi`.

That turned out to be a bit annoying, since the heap is fucking with me, so i'll jus try to get another info leak, this time for the pwnable.kr `libc`.

Returning to the stack-info-leak strategy, after a bit of digging, I found the info leak I wanted in `%10$llx`.

Victory!
