# Dragon

After a bit of digging around I identified two structures, roughly equivalent to the following:

```c
struct Dragon {
    void (*print_func)(struct Dragon*);
    uint32_t type;
    uint8_t hp;
    uint8_t regen;
    uint16_t pad1;
    uint32_t damage;
}

struct Player {
    uint32_t type;
    uint32_t hp;
    uint32_t mana;
    void (*print_func)(struct Player*);
}
```

This led me immediatly to look for something like type confusion.

Actually, the first thing that looked strange in this binary is the fact that a `Dragon` structure and a `Player` are allocated on the heap in `FightDragon()`, but the `Player` is the only one `free`'d in that function.

Actually, the `Dragon` structure is `free`'d in an inner function, `KnightAttack()` or `PriestAttack()`.

This seemed really strange. After some more digging around we can see that this bug can lead to arbitrary code exectued, since that `Dragon` is used again in `FightDragon()` after it's `free`'d.

Since we allocate another 16 bit long buffer on the heap, and we control it, we can override the saved `print_func()` function and call whatever we want.

For example, we can use the `system("/bin/sh")` opcodes in `SecretLevel()`, and get a shell.

Notice that since `Dragon.hp` is only 1 byte long, we can pretty easily get it to overflow and win the game.

Victory!
