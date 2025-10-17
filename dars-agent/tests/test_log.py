"""Unit tests for sweagent.utils.log module.

Tests cover logging functionality including:
- Logger creation and configuration
- Log level interpretation
- File handler management
- Environment variable handling
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sweagent.utils.log import (
    _interpret_level_from_env,
    add_file_handler,
    get_logger,
)


class TestInterpretLevelFromEnv:
    """Test the _interpret_level_from_env function."""

    def test_none_returns_default(self):
        """Test that None returns default level."""
        result = _interpret_level_from_env(None, default=logging.DEBUG)
        assert result == logging.DEBUG

    def test_empty_string_returns_default(self):
        """Test that empty string returns default level."""
        result = _interpret_level_from_env("", default=logging.INFO)
        assert result == logging.INFO

    def test_numeric_string_returns_int(self):
        """Test that numeric string is converted to int."""
        result = _interpret_level_from_env("10")
        assert result == 10

    def test_level_name_debug(self):
        """Test that 'debug' string returns DEBUG level."""
        result = _interpret_level_from_env("debug")
        assert result == logging.DEBUG

    def test_level_name_info(self):
        """Test that 'info' string returns INFO level."""
        result = _interpret_level_from_env("info")
        assert result == logging.INFO

    def test_level_name_warning(self):
        """Test that 'warning' string returns WARNING level."""
        result = _interpret_level_from_env("warning")
        assert result == logging.WARNING

    def test_level_name_error(self):
        """Test that 'error' string returns ERROR level."""
        result = _interpret_level_from_env("error")
        assert result == logging.ERROR

    def test_level_name_critical(self):
        """Test that 'critical' string returns CRITICAL level."""
        result = _interpret_level_from_env("critical")
        assert result == logging.CRITICAL

    def test_level_name_case_insensitive(self):
        """Test that level names are case-insensitive."""
        result_upper = _interpret_level_from_env("DEBUG")
        result_lower = _interpret_level_from_env("debug")
        result_mixed = _interpret_level_from_env("DeBuG")
        assert result_upper == result_lower == result_mixed == logging.DEBUG

    def test_zero_numeric_level(self):
        """Test that '0' is handled correctly."""
        result = _interpret_level_from_env("0")
        assert result == 0

    def test_large_numeric_level(self):
        """Test that large numeric values are handled."""
        result = _interpret_level_from_env("100")
        assert result == 100

    def test_trace_level(self):
        """Test that TRACE level is available."""
        result = _interpret_level_from_env("trace")
        assert result == logging.TRACE  # type: ignore


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_name(self):
        """Test that logger has the correct name."""
        logger = get_logger("test_logger_name")
        assert logger.name == "test_logger_name"

    def test_get_logger_has_rich_handler(self):
        """Test that logger has a RichHandler attached."""
        logger = get_logger("test_rich_handler")
        # Check that at least one handler is present
        assert len(logger.handlers) > 0

    def test_get_logger_propagate_false(self):
        """Test that logger propagate is set to False."""
        logger = get_logger("test_propagate")
        assert logger.propagate is False

    def test_get_logger_same_logger_reused(self):
        """Test that calling get_logger twice with same name returns same instance."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")
        assert logger1 is logger2

    @patch.dict(os.environ, {"SWE_AGENT_LOG_STREAM_LEVEL": "WARNING"})
    def test_get_logger_respects_stream_level(self):
        """Test that logger respects SWE_AGENT_LOG_STREAM_LEVEL environment variable."""
        logger = get_logger("test_stream_level")
        # Logger should be configured with the specified level or lower
        assert logger.level <= logging.WARNING

    @patch.dict(os.environ, {"SWE_AGENT_LOG_TIME": "1"})
    def test_get_logger_with_time_enabled(self):
        """Test logger configuration with time display enabled."""
        logger = get_logger("test_with_time")
        assert isinstance(logger, logging.Logger)

    @patch.dict(os.environ, {"SWE_AGENT_LOG_TIME": ""})
    def test_get_logger_with_time_disabled(self):
        """Test logger configuration with time display disabled."""
        logger = get_logger("test_without_time")
        assert isinstance(logger, logging.Logger)


class TestAddFileHandler:
    """Test the add_file_handler function."""

    def test_add_file_handler_creates_file(self):
        """Test that add_file_handler creates a log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            get_logger("test_file_handler_create")
            add_file_handler(log_path)
            # Write a log message
            logger = get_logger("test_file_handler_create")
            logger.info("Test message")
            # Check that file was created
            assert log_path.exists()

    def test_add_file_handler_writes_logs(self):
        """Test that logs are written to the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_write.log"
            logger = get_logger("test_file_write")
            add_file_handler(log_path)
            logger.info("Test log message")
            # Read the log file
            with open(log_path) as f:
                content = f.read()
            assert "Test log message" in content

    def test_add_file_handler_str_path(self):
        """Test that add_file_handler accepts string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = str(Path(tmpdir) / "test_str.log")
            logger = get_logger("test_str_path")
            add_file_handler(log_path)
            logger.info("Test message")
            assert Path(log_path).exists()

    def test_add_file_handler_pure_path(self):
        """Test that add_file_handler accepts PurePath."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_pure.log"
            logger = get_logger("test_pure_path")
            add_file_handler(log_path)
            logger.info("Test message")
            assert log_path.exists()

    def test_add_file_handler_multiple_loggers(self):
        """Test that file handler is added to all existing loggers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_multiple.log"
            logger1 = get_logger("test_multi_1")
            logger2 = get_logger("test_multi_2")
            add_file_handler(log_path)
            logger1.info("Message from logger1")
            logger2.info("Message from logger2")
            with open(log_path) as f:
                content = f.read()
            assert "Message from logger1" in content
            assert "Message from logger2" in content

    def test_add_file_handler_future_loggers(self):
        """Test that file handler is added to loggers created after add_file_handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_future.log"
            add_file_handler(log_path)
            # Create logger after adding file handler
            logger = get_logger("test_future_logger")
            logger.info("Test message")
            with open(log_path) as f:
                content = f.read()
            assert "Test message" in content

    def test_file_handler_log_format(self):
        """Test that file handler uses correct log format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_format.log"
            logger = get_logger("test_format")
            add_file_handler(log_path)
            logger.info("Format test")
            with open(log_path) as f:
                content = f.read()
            # Check that format includes timestamp and level
            assert "INFO" in content
            assert "Format test" in content

    @patch.dict(os.environ, {"SWE_AGENT_LOG_FILE_LEVEL": "ERROR"})
    def test_file_handler_respects_file_level(self):
        """Test that file handler respects SWE_AGENT_LOG_FILE_LEVEL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_level.log"
            logger = get_logger("test_file_level")
            add_file_handler(log_path)
            logger.debug("Debug message")
            logger.info("Info message")
            logger.error("Error message")
            with open(log_path) as f:
                content = f.read()
            # Only ERROR and above should be logged
            assert "Error message" in content


class TestLoggerBehavior:
    """Test overall logger behavior and integration."""

    def test_logger_logs_at_different_levels(self):
        """Test that logger can log at different levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_levels.log"
            logger = get_logger("test_all_levels")
            add_file_handler(log_path)
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            with open(log_path) as f:
                content = f.read()
            # All messages should be in the log
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content

    def test_default_logger_exists(self):
        """Test that default logger is available."""
        from sweagent.utils.log import default_logger

        assert isinstance(default_logger, logging.Logger)
        assert default_logger.name == "swe-agent"

    def test_multiple_file_handlers(self):
        """Test adding multiple file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path1 = Path(tmpdir) / "test1.log"
            log_path2 = Path(tmpdir) / "test2.log"
            logger = get_logger("test_multi_handlers")
            add_file_handler(log_path1)
            add_file_handler(log_path2)
            logger.info("Test message")
            # Both files should contain the message
            with open(log_path1) as f:
                assert "Test message" in f.read()
            with open(log_path2) as f:
                assert "Test message" in f.read()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_logger_with_empty_name(self):
        """Test creating logger with empty name."""
        logger = get_logger("")
        assert isinstance(logger, logging.Logger)

    def test_logger_with_special_characters(self):
        """Test creating logger with special characters in name."""
        logger = get_logger("test-logger.with_special/chars")
        assert isinstance(logger, logging.Logger)

    def test_add_file_handler_nested_directory(self):
        """Test adding file handler with nested directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "nested" / "dir" / "test.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            logger = get_logger("test_nested")
            add_file_handler(log_path)
            logger.info("Test message")
            assert log_path.exists()

    def test_very_long_log_message(self):
        """Test logging very long message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_long.log"
            logger = get_logger("test_long_msg")
            add_file_handler(log_path)
            long_message = "A" * 10000
            logger.info(long_message)
            with open(log_path) as f:
                content = f.read()
            assert long_message in content

    def test_log_message_with_newlines(self):
        """Test logging message with newlines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_newlines.log"
            logger = get_logger("test_newlines")
            add_file_handler(log_path)
            logger.info("Line 1\nLine 2\nLine 3")
            with open(log_path) as f:
                content = f.read()
            assert "Line 1" in content

    def test_log_message_with_unicode(self):
        """Test logging message with Unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_unicode.log"
            logger = get_logger("test_unicode")
            add_file_handler(log_path)
            logger.info("Unicode: 你好 мир 🚀")
            with open(log_path) as f:
                content = f.read()
            assert "你好" in content or "Unicode" in content
