import logging
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

logger = logging.getLogger('bw_logger')

@require_http_methods(["GET"])
def test_logging(request):
    """
    Test view to verify logging configuration works with django-log-viewer
    """
    logger.info("Test info message - logging setup verification")
    logger.warning("Test warning message - potential issue detected")
    
    try:
        # Simulate an error with traceback
        raise ValueError("This is a test error to verify traceback capture")
    except Exception as e:
        logger.exception("Test error occurred - full traceback should be captured")
        logger.error("Test error message without exception", exc_info=True)
    
    logger.debug("Test debug message - detailed information")
    logger.critical("Test critical message - system failure simulation")
    
    return HttpResponse("""
        <h1>Logging Test Completed</h1>
        <p>Check django-log-viewer to see the following log entries:</p>
        <ul>
            <li>INFO message</li>
            <li>WARNING message</li>
            <li>ERROR with full traceback (exception)</li>
            <li>ERROR with exc_info=True</li>
            <li>DEBUG message</li>
            <li>CRITICAL message</li>
        </ul>
        <p>All logs should be in JSON format with complete error details.</p>
    """)
