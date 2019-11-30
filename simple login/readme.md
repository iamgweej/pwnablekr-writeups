# Simple Login

## Theory

In `auth()` we have a buffer overflow that lets us override the saved `ebp` of the previous frame.

We can see that there are no refrences to `ebp` in the `main()` function until it `leave`'s, so we can safely modify it without causing a crash.

Now, when `main()` `leave`'s, that `ebp` will be moved to `esp`, and when payload`main()` `retn`'s, it will set `eip` to `[esp]`.

Notice that `0x8049284` is the address of the call `system("bin/sh")`, so we would probably want to jump there. 

So, if we put a payload of this sort: `"AAAA<new-eip=0x8049284><&new-eip+4>"` the program should execute like this:

* In `auth()`'s frame:
  * We overflow the stored `main-ebp` on the stack, making it point to where we stored `new-eip`, that is, the address `0x8049284`
  * When `auth()` `leave`'s, `main()`'s `ebp` is restored and now is to `&new-eip+4`.
* In `main()`'s frame:
  * `ebp` is not used, so we have no problem of messing up the function.
  * When `main()` `leave`'s, `esp` now points to `&new-eip+4`.
  * When `main()` `retn`'s, `eip` will be `new-eip` (since a `retn` is like a `pop eip`).
* `system("/bin/sh")` will be executed. Victory!
