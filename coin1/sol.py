import re
import math

from pwn import *

HEADER = "	- Ready? starting in 3 sec... -\n\t\n"
N_C_PATTERN = re.compile(r"N=([0-9]+) C=([0-9]+)")


class CoinQuiz(object):
    """
    A class representing and instance of a coin quiz game.
    """

    def __init__(self, conn):
        self._conn = conn

        line = self._conn.recvline().strip()
        self._n, self._c = re.match(N_C_PATTERN, line).group(1, 2)
        self._n, self._c = int(self._n), int(self._c)
        assert math.log(float(self._n), 2) <= self._c

    @property
    def n(self):
        return self._n

    @property
    def c(self):
        return self._c

    def weigh(self, coins):
        """
        :param coins: A list of coin indice to weigh
        :return: The combined weight of those coins
        """

        assert self._c > 0

        message = ' '.join(str(i) for i in coins)
        self._conn.sendline(message)
        self._c -= 1
        return(int(self._conn.readline().strip()))


def solve_quiz(cq):
    assert isinstance(cq, CoinQuiz)

    options = range(cq.n)
    #print options

    while len(options) > 1:
        #print options
        test_options = [j for i, j in enumerate(options) if i % 2 == 1]
        other = [j for i, j in enumerate(options) if i % 2 == 0]
        weight = cq.weigh(test_options)
        #print weight
        if weight % 10 == 9:
            options = test_options
        else:
            options = other

    while cq.c != 0:
        cq.weigh([0])

    return options[0]


def main():
    conn = remote('pwnable.kr', 9007)
    conn.recvuntil(HEADER)

    for i in xrange(100):
        cq = CoinQuiz(conn)
        print "[+] ({i}) N: {n}, C: {c}".format(i=i, n=cq.n, c=cq.c)
        solution = solve_quiz(cq)
        print "[+] ({i}) Sol: {s}".format(i=i, s=solution)
        conn.sendline(str(solution))
        line = conn.recvline()
        print "[+] ({i}) Recieved: {r}".format(i=i, r=repr(line))

    conn.interactive()


if __name__ == "__main__":
    main()
