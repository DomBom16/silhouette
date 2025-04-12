import datetime
from colorama import Fore, Back, Style, init
import wcwidth

init(autoreset=True)

colors = {
    "DEBUG": Fore.BLUE,
    "INFO": Fore.WHITE,
    "SUCCESS": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.WHITE + Back.RED + Style.BRIGHT,
}


def rendered_width(string):
    width = 0
    for char in string:
        width += wcwidth.wcwidth(char)
    return width


class AsyncLogger:
    def __init__(self):
        """AsyncLogger can be used to asynchronously log messages to the console line"""
        self.prev_log = None
        self.prev_level = None
        self.prev_time_format = None
        self.log_count = 0
        self.log_len = 0

    async def log(self, level, message, time_format):
        """Low-level log method that logs a message to the console."""

        timestamp = datetime.datetime.now().strftime(time_format)
        time_colored = f"{Fore.GREEN}{timestamp}{Style.RESET_ALL}"

        padded_level = level.upper().ljust(8)

        formatted_message = (
            f"\033[2K{time_colored} {colors[level]}{padded_level} {message}"
        )

        if (
            message == self.prev_log
            and level != "CRITICAL"
            and level == self.prev_level
            and time_format == self.prev_time_format
        ):
            self.log_count += 1
        else:
            print(formatted_message)
            self.prev_log = message
            self.prev_level = level
            self.prev_time_format = time_format
            self.log_count = 1
            self.log_len = rendered_width(f"{timestamp} {padded_level} {message}")

    async def debug(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a DEBUG message."""

        await self.log("DEBUG", message, time_format=time_format)
        await self.close(time_format=time_format)

    async def info(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log an INFO message."""

        await self.log("INFO", message, time_format=time_format)
        await self.close(time_format=time_format)

    async def success(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a SUCCESS message."""

        await self.log("SUCCESS", message, time_format=time_format)
        await self.close(time_format=time_format)

    async def warning(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a WARNING message."""

        await self.log("WARNING", message, time_format=time_format)
        await self.close(time_format=time_format)

    async def error(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log an ERROR message."""

        await self.log("ERROR", message, time_format=time_format)
        await self.close(time_format=time_format)

    async def critical(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a CRITICAL message."""

        await self.log("CRITICAL", message, time_format=time_format)
        await self.close(time_format=time_format)

    async def close(self, time_format):
        timestamp = datetime.datetime.now().strftime(time_format)
        time_colored = f"{Fore.GREEN}{timestamp}{Style.RESET_ALL}"

        if self.prev_log is not None and self.log_count > 1:
            print("\033[1A" + time_colored)
            print(
                " " * self.log_len
                + f"\033[1A {Style.DIM}{Fore.WHITE}(x{self.log_count}){Style.RESET_ALL}"
            )
            print(
                " " * self.log_len
                + f"\033[1A {Style.DIM}{Fore.WHITE}(x{self.log_count}){Style.RESET_ALL}"
            )


class Logger:
    def __init__(self):
        """Logger can be used to synchronously log messages to the console line"""
        self.prev_log = None
        self.prev_level = None
        self.prev_time_format = None
        self.log_count = 0
        self.log_len = 0

    def log(self, level, message, time_format):
        """Low-level log method that logs a message to the console."""

        timestamp = datetime.datetime.now().strftime(time_format)
        time_colored = f"{Fore.GREEN}{timestamp}{Style.RESET_ALL}"

        padded_level = level.upper().ljust(8)

        formatted_message = (
            f"\033[2K{time_colored} {colors[level]}{padded_level} {message}"
        )

        if (
            message == self.prev_log
            and level != "CRITICAL"
            and level == self.prev_level
            and time_format == self.prev_time_format
        ):
            self.log_count += 1
        else:
            print(formatted_message)
            self.prev_log = message
            self.prev_level = level
            self.prev_time_format = time_format
            self.log_count = 1
            self.log_len = rendered_width(f"{timestamp} {padded_level} {message}")

    def debug(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a DEBUG message."""

        self.log("DEBUG", message, time_format=time_format)
        self.close(time_format=time_format)

    def info(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log an INFO message."""

        self.log("INFO", message, time_format=time_format)
        self.close(time_format=time_format)

    def success(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a SUCCESS message."""

        self.log("SUCCESS", message, time_format=time_format)
        self.close(time_format=time_format)

    def warning(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a WARNING message."""

        self.log("WARNING", message, time_format=time_format)
        self.close(time_format=time_format)

    def error(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log an ERROR message."""

        self.log("ERROR", message, time_format=time_format)
        self.close(time_format=time_format)

    def critical(self, message, time_format="%Y-%m-%d %H:%M:%S"):
        """Log a CRITICAL message."""

        self.log("CRITICAL", message, time_format=time_format)
        self.close(time_format=time_format)

    def close(self, time_format):
        timestamp = datetime.datetime.now().strftime(time_format)
        time_colored = f"{Fore.GREEN}{timestamp}{Style.RESET_ALL}"

        if self.prev_log is not None and self.log_count > 1:
            print("\033[1A" + time_colored)
            print(
                " " * self.log_len
                + f"\033[1A {Style.DIM}{Fore.WHITE}(x{self.log_count}){Style.RESET_ALL}"
            )
