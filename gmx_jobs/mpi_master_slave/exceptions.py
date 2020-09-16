class SlaveNotReady(Exception):
    """Raise when attempting to give a non-ready slave a job"""


class JobFailedException(Exception):
    """Raise by the master when a slave fails a job"""
