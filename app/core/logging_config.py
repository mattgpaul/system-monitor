"""
Logging configuration for the telemetry system.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the entire telemetry system."""
    
    # Get the root telemetry logger
    logger = logging.getLogger("telemetry_agent")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger (avoids double logging)
    logger.propagate = False