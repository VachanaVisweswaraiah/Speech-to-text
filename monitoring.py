"""
Logging and monitoring utilities.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Logs directory
LOGS_DIR = Path("logs")


def initialize_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize application logging.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file (str, optional): Log file path. If None, uses default.

    Returns:
        logging.Logger: Configured logger instance.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Get log level from environment or parameter
    level_str = os.getenv("LOG_LEVEL", log_level).upper()
    level = getattr(logging, level_str, logging.INFO)

    # Create logger
    app_logger = logging.getLogger("speech-to-text")
    app_logger.setLevel(level)

    # Remove existing handlers
    app_logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_file = LOGS_DIR / log_file

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    return app_logger


# Global logger instance
logger = initialize_logging()


def log_event(
    event_type: str,
    username: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
) -> None:
    """
    Log application event.

    Args:
        event_type (str): Type of event (e.g., 'login', 'transcribe', 'error').
        username (str, optional): Username associated with event.
        details (Dict, optional): Additional event details.
        severity (str): Log severity level.
    """
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "username": username,
        "details": details or {},
    }

    log_method = getattr(logger, severity.lower(), logger.info)
    log_method("%s: %s", event_type, json.dumps(event_data))


def log_transcription(
    username: str, filename: str, duration_seconds: float, status: str = "success"
) -> None:
    """
    Log transcription event.

    Args:
        username (str): Username.
        filename (str): Audio filename.
        duration_seconds (float): Audio duration in seconds.
        status (str): Transcription status (success, failed, etc.).
    """
    log_event(
        "transcribe",
        username,
        {
            "filename": filename,
            "duration": duration_seconds,
            "status": status,
        },
    )


def log_auth_event(username: str, event: str, success: bool = True) -> None:
    """
    Log authentication event.

    Args:
        username (str): Username.
        event (str): Auth event (login, logout, signup, password_change).
        success (bool): Whether event was successful.
    """
    log_event(
        "auth",
        username,
        {
            "event": event,
            "success": success,
        },
    )


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """
    Log error with context.

    Args:
        error (Exception): Exception object.
        context (str, optional): Additional context information.
    """
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
    }

    logger.error("Error: %s", json.dumps(error_data), exc_info=True)


def get_logs(log_file: Optional[str] = None, lines: int = 100) -> list:
    """
    Get recent log lines.

    Args:
        log_file (str, optional): Specific log file. If None, uses today's log.
        lines (int): Number of recent lines to return.

    Returns:
        list: List of log lines.
    """
    if log_file is None:
        log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_file = LOGS_DIR / log_file

    if not log_file.exists():
        return []

    with open(log_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    return all_lines[-lines:]


def cleanup_old_logs(days: int = 30) -> int:
    """
    Clean up log files older than specified days.

    Args:
        days (int): Delete logs older than this many days.

    Returns:
        int: Number of files deleted.
    """
    cutoff = datetime.now() - timedelta(days=days)
    deleted_count = 0

    if not LOGS_DIR.exists():
        return 0

    for log_file in LOGS_DIR.glob("*.log"):
        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
            log_file.unlink()
            deleted_count += 1

    return deleted_count


class PerformanceMonitor:
    """Monitor and track application performance metrics."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics_file = LOGS_DIR / "metrics.json"
        self._ensure_metrics_file()

    def _ensure_metrics_file(self) -> None:
        """Ensure metrics file exists."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.metrics_file.exists():
            self.metrics_file.write_text(
                json.dumps({"transcriptions": []}, indent=2),
                encoding="utf-8",
            )

    def record_transcription(
        self,
        username: str,
        duration_seconds: float,
        processing_time_seconds: float,
        chunks: int = 1,
    ) -> None:
        """
        Record transcription metrics.

        Args:
            username (str): Username.
            duration_seconds (float): Audio duration in seconds.
            processing_time_seconds (float): Time to process in seconds.
            chunks (int): Number of chunks processed.
        """
        with open(self.metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        metric_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "audio_duration": duration_seconds,
            "processing_time": processing_time_seconds,
            "chunks": chunks,
            "efficiency": (
                duration_seconds / processing_time_seconds if processing_time_seconds > 0 else 0
            ),
        }

        metrics["transcriptions"].append(metric_entry)

        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated performance statistics.

        Returns:
            Dict: Performance statistics.
        """
        with open(self.metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        transcriptions = metrics.get("transcriptions", [])

        if not transcriptions:
            return {
                "total_transcriptions": 0,
                "avg_processing_time": 0,
                "avg_efficiency": 0,
            }

        processing_times = [t["processing_time"] for t in transcriptions]
        efficiencies = [t["efficiency"] for t in transcriptions]

        return {
            "total_transcriptions": len(transcriptions),
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "avg_efficiency": sum(efficiencies) / len(efficiencies),
            "total_audio_processed": sum(t["audio_duration"] for t in transcriptions),
        }


# Global performance monitor instance
perf_monitor = PerformanceMonitor()
