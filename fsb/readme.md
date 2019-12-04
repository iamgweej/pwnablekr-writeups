# FSB

I guess `fsb` stands for Format String Bug?

Looks like a format string bug with a twist.

We have a pointer to the stack somewhere on the stack (the `pargv` variable, for example), and using the `%n` format, we can write any integer value we want to it, for example, the address of `key`.

Afterwards, we'll find the data we wrote on the stack and use the `%n` format again to write `0` to it, effectively zero-ing out `key`.

We need to this twice since `key` is a `long long`.

Afterwards, entering `0` should get us a shell.

Victory!
