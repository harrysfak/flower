import psutil

CPU_LIMIT = 80


class CPULimitExceeded(Exception):
    pass
