import time
from functools import wraps

from src.utils import logger


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        elapsed = end - start
        minutes, seconds = divmod(elapsed, 60)
        logger.info(
            f"Execution time of {func.__name__}(): {int(minutes)}m {seconds:.2f}s"
        )
        return result

    return wrapper
