import traceback
from src.services.email_service import EmailService

def handle_error(error: Exception, logger, email_service: EmailService):
    """Handle any errors that occur during report generation. Tries to send an email notification. """
    error_message = f"Error details:\n{str(error)}\n\nTraceback:\n{traceback.format_exc()}"
    logger.error(str(error))
    logger.debug(error_message)
    try: 
        email_service.send_error(error_message)
    except Exception as email_error:
        logger.error(f"Failed to send error email: {str(email_error)}")