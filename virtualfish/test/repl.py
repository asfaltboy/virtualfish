"""Interact with a Fish REPL.
"""

import os
import subprocess
from subprocess import PIPE
import time
from queue import Queue
from threading import Thread

def write_thread(q, f):
    while True:
        data = q.get()
        f.write(data)
        f.flush()

def read_thread(f, q):
    while True:
        data = f.read(1)
        q.put(data)

def write(f):
    q = Queue()
    t = Thread(target=write_thread, args=(q, f))
    t.daemon = True
    t.start()
    return q

def read(f):
    q = Queue()
    t = Thread(target=read_thread, args=(f, q))
    t.daemon = True
    t.start()
    return q

def q_until_null(q):
    ba = bytearray()
    while True:
        c = q.get()
        if c == b'\0':
            return bytes(ba)
        ba.append(c[0])


class Fish:
    """A Fish instance running a custom REPL in a subprocess.

    Each instance of this class has its own subprocess, with its own
    state (variables, loaded functions, etc).
    """
    def __init__(self):
        # Start Fish up with our custom REPL. We don't use the built-in
        # REPL because if we run Fish non-interactively we can't tell
        # the difference between Fish waiting for input and whatever
        # command we ran waiting for something else, and if we run it
        # in a pty we'd have to correctly handle the fish_prompt, fish
        # echoing back our input (and possibly even syntax highlighting
        # it), and so on.
        self.subp = subprocess.Popen(
            (
                "/usr/local/Cellar/fish/2.4.0/bin/fish", 
                os.path.join(os.path.dirname(__file__), 'repl.fish'),
            ),
            stdin=PIPE, stdout=PIPE, stderr=PIPE,
        )
        # We read and write to/from stdin/out/err in threads, to prevent
        # deadlocks (see the warning in the subprocess docs).
        self.stdin_q = write(self.subp.stdin)
        self.stdout_q = read(self.subp.stdout)
        self.stderr_q = read(self.subp.stderr)
    
    def run(self, cmd):
        """Run a command on the REPL.

        The command can do anything except read from standard input
        (because there's currently no way for the test case to write
        into it) or print a null byte (since that's how the REPL signals
        that the command has finished).

        :param cmd: The command to run.
        :type cmd: str|bytes
        :return: Standard output, standard error, return code.
        :rtype: Tuple[bytes, bytes, int]
        """
        if isinstance(cmd, str):
            cmd = cmd.encode('utf8')
        self.stdin_q.put(cmd)
        self.stdin_q.put(b'\0')
        output = q_until_null(self.stdout_q)
        error = q_until_null(self.stderr_q)
        status = int(q_until_null(self.stdout_q).decode('utf8'))
        return output, error, status

if __name__ == "__main__":
    # If invoked directly, executes a bunch of simple test commands.
    # This is to make 
    f = Fish()
    print(f.run("echo 1"))
    print(f.run("echo 1 >&2"))
    print(f.run("set foo bar"))
    print(f.run("echo $foo"))
    print(f.run("false"))