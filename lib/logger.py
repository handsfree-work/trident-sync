from sys import stdout

import loguru

logger = loguru.logger
logger.remove(0)
logger.add(stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:7}</level> | - <level>{message}</level>", colorize=True)
