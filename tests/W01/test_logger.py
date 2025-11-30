"""Test logging module"""
from src.utils.logger import setup_logging, get_logger, log_info, log_warning, log_error, LogTimer
import time

def test_logger():
    print("="*70)
    print("Testing Logger Module")
    print("="*70)
    
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Test different log levels
    print("\nTesting log levels (check console colors):")
    logger.debug("This is a DEBUG message (cyan)")
    logger.info("This is an INFO message (green)")
    logger.warning("This is a WARNING message (yellow)")
    logger.error("This is an ERROR message (red)")
    
    # Test convenience functions
    print("\nTesting convenience functions:")
    log_info("Using log_info convenience function")
    log_warning("Using log_warning convenience function")
    log_error("Using log_error convenience function")
    
    # Test LogTimer
    print("\nTesting LogTimer context manager:")
    with LogTimer("Test operation"):
        time.sleep(1)
    
    print("\n" + "="*70)
    print("✓✓✓ Logger module works correctly!")
    print("="*70)
    print("\nCheck that:")
    print("  - Messages appeared in console with colors")
    print("  - Messages were written to logs/dragon_codex.log")
    print("  - LogTimer showed elapsed time")

if __name__ == "__main__":
    test_logger()