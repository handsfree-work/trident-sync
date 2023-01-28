from sys import stdout

import loguru

logger = loguru.logger
logger.remove(0)
logger.add(stdout, format="<level>{time:YYYY-MM-DD HH:mm:ss} | {level:7} | - {message}</level>", colorize=True)
