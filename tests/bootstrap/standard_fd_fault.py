"""Test-only bad-FD setup across Linux and Android host-runtime startup."""
import os
import sys


def invalidate_standard_fd(number):
    if number not in (0, 1, 2):
        raise ValueError("fault fixture requires standard descriptor 0, 1 or 2")
    if sys.platform != "android":
        os.close(number)
        return
    # Bionic may reopen absent standard FDs before QEMU/host Python starts.
    # A live descriptor with the wrong access mode survives and yields EBADF.
    descriptor = os.open(os.devnull, os.O_WRONLY if number == 0 else os.O_RDONLY)
    try:
        os.dup2(descriptor, number)
        os.set_inheritable(number, True)
    finally:
        if descriptor != number:
            os.close(descriptor)
