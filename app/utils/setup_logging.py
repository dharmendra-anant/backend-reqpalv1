import json
import logging
import logging.config
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """JSON formatter with clean, structured output and complex object handling"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "logger": record.name,
            "level": record.levelname,
            "file": record.filename,
            "line": record.lineno,
            "message": record.msg,
        }

        if hasattr(record, "context"):
            log_data["context"] = self._sanitize_value(record.context)
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, indent=2, default=str)

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize values for JSON serialization"""
        if isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize_value(v) for v in value]
        if hasattr(value, "model_dump"):  # Pydantic v2
            return value.model_dump()
        if hasattr(value, "dict"):  # Pydantic v1
            return value.dict()
        try:
            json.dumps(value)
            return value
        except Exception:
            return str(value)


class ColoredConsoleFormatter(JsonFormatter):
    """Enhanced console formatter with color support and optional compact output"""

    COLORS = {
        "DEBUG": "\x1b[38;20m",  # grey
        "INFO": "\x1b[32;20m",  # green
        "WARNING": "\x1b[33;20m",  # yellow
        "ERROR": "\x1b[31;20m",  # red
        "CRITICAL": "\x1b[31;1m",  # bold red
    }
    RESET = "\x1b[0m"

    def __init__(self, compact: bool = True):
        super().__init__()
        self.compact = compact

    def format(self, record: logging.LogRecord) -> str:
        if self.compact:
            # Simplified output for console
            msg = f"[{record.levelname}] {record.name}: {record.getMessage()}"
            if hasattr(record, "context"):
                msg += f" | context: {self._sanitize_value(record.context)}"
        else:
            msg = super().format(record)

        color = self.COLORS.get(record.levelname, self.COLORS["DEBUG"])
        return f"{color}{msg}{self.RESET}"


class JsonArrayFileHandler(logging.FileHandler):
    """File handler that maintains a proper JSON array format"""

    def __init__(self, filename: str, mode: str = "a", encoding: Optional[str] = None):
        # Ensure log directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        super().__init__(filename, mode, encoding)
        if mode == "w" or (mode == "a" and self.stream.tell() == 0):
            self.stream.write("[\n")
        elif mode == "a":
            self.stream.seek(self.stream.tell() - 2, 0)
            self.stream.write(",\n\n")

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.stream.write(msg)
        self.stream.write(",\n\n")
        self.flush()

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.seek(self.stream.tell() - 3, 0)
            self.stream.write("\n]\n")
        super().close()


def setup_logging(
    debug: bool = False,
    log_file: str = "logs/app.log",
    module_levels: Optional[Dict[str, str]] = None,
    compact_console: bool = True,
) -> None:
    """
    Configure application logging with enhanced control over log levels

    Args:
        debug: Enable debug logging globally
        log_file: Path to log file
        module_levels: Dict of logger names and their levels (e.g., {"api": "DEBUG", "db": "INFO"})
        compact_console: Use compact console output instead of full JSON
    """
    # Create formatters
    console_formatter = ColoredConsoleFormatter(compact=compact_console)
    file_formatter = JsonFormatter()

    # Configure handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    file_handler = JsonArrayFileHandler(log_file, mode="a")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)

    # Configure app logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    app_logger.propagate = False
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)

    # Set custom levels for specific modules
    if module_levels:
        for logger_name, level in module_levels.items():
            logging.getLogger(logger_name).setLevel(getattr(logging, level.upper()))

    # Configure common third-party loggers
    for logger_name in ["urllib3", "asyncio", "websockets", "httpx"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
