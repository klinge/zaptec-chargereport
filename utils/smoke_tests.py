#!/usr/bin/env python3
"""
Smoke tests to verify production deployment is working correctly.
Run after deployment to catch critical issues quickly.
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global shared API instance to avoid rate limiting from multiple authentications
_shared_api_instance = None

def setup_smoke_test_logger():
    """Setup simple logger for smoke tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - SMOKE TEST - %(levelname)s - %(message)s'
    )
    return logging.getLogger('smoke_test')

def get_shared_api_instance():
    """Get or create a shared ZaptecApi instance to avoid rate limiting"""
    global _shared_api_instance
    if _shared_api_instance is None:
        from src.api.zaptec_api import ZaptecApi
        _shared_api_instance = ZaptecApi()
    return _shared_api_instance

def cleanup_shared_api_instance():
    """Clean up the shared API instance"""
    global _shared_api_instance
    if _shared_api_instance is not None:
        _shared_api_instance.session.close()
        _shared_api_instance = None

def test_environment_variables():
    """Verify all required environment variables are present"""
    logger = setup_smoke_test_logger()
    logger.info("Testing environment variables...")
    
    required_vars = [
        'ZAPTEC_USERNAME', 'ZAPTEC_PASSWORD', 'ZAPTEC_INSTALLATION_ID',
        'CHARGING_TARIFF', 'DATA_DIR', 'REPORT_FILE'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✓ All required environment variables present")
    return True

def test_directory_structure():
    """Verify required directories exist and are writable"""
    logger = setup_smoke_test_logger()
    logger.info("Testing directory structure...")
    
    data_dir = os.getenv('DATA_DIR', 'data')
    required_dirs = [
        f"{data_dir}/logs",
        f"{data_dir}/reports"
    ]
    
    for dir_path in required_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            # Test write permission
            test_file = f"{dir_path}/.smoke_test"
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            logger.error(f"Directory issue with {dir_path}: {e}")
            return False
    
    logger.info("✓ Directory structure OK")
    return True

def test_imports():
    """Verify all critical modules can be imported"""
    logger = setup_smoke_test_logger()
    logger.info("Testing module imports...")
    
    try:
        from src.api.zaptec_api import ZaptecApi
        from src.reports.invoicing_report import InvoicingReport
        from src.reports.monthly_summary_report import MonthlySummaryReport
        from src.services.email_service import EmailService
        from src.utils.logger import setup_logger
        from src.utils.dateutils import get_previous_month_range
        logger.info("✓ All modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False

def test_zaptec_api_connection():
    """Test basic connectivity to Zaptec API (authentication only)"""
    logger = setup_smoke_test_logger()
    logger.info("Testing Zaptec API connection...")
    
    try:
        api = get_shared_api_instance()
        # Just test authentication, don't fetch data
        token_data = api.get_auth_token()
        if token_data.get('access_token'):
            logger.info("✓ Zaptec API authentication successful")
            return True
        else:
            logger.error("No access token received")
            return False
    except Exception as e:
        logger.error(f"Zaptec API connection failed: {e}")
        return False

def test_api_structure_quick_check():
    """Quick check that API structure hasn't changed (pagination, etc.)"""
    logger = setup_smoke_test_logger()
    logger.info("Testing API structure...")
    
    try:
        from src.utils.dateutils import get_previous_month_range
        
        # Use last 7 days to minimize data
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        from_date = start_date.strftime("%Y-%m-%dT00:00:00.001Z")
        to_date = end_date.strftime("%Y-%m-%dT23:59:59.999Z")
        
        api = get_shared_api_instance()
        response = api.get_charging_sessions(from_date, to_date)
        
        # Verify pagination is working (should handle multiple pages fine)
        if hasattr(response, 'Pages'):
            if response.Pages > 1:
                logger.info(f"✓ Pagination working: {len(response.Data)} items across {response.Pages} pages")
            else:
                logger.info(f"✓ Single page response: {len(response.Data)} items")
        else:
            logger.error("API response missing 'Pages' field - structure changed!")
            return False
            
        logger.info("✓ API structure check passed")
        return True
        
    except Exception as e:
        logger.error(f"API structure check failed: {e}")
        return False

def test_email_service_config():
    """Test email service configuration (don't send actual email)"""
    logger = setup_smoke_test_logger()
    logger.info("Testing email service configuration...")
    
    try:
        from src.services.email_service import EmailService
        email_service = EmailService()
        
        # Verify SMTP settings are configured
        if not all([email_service.smtp_server, email_service.smtp_username, 
                   email_service.smtp_password, email_service.smtp_from]):
            logger.error("SMTP configuration incomplete")
            return False
            
        logger.info("✓ Email service configuration OK")
        return True
    except Exception as e:
        logger.error(f"Email service configuration error: {e}")
        return False

def test_date_calculations():
    """Test date utility functions work correctly"""
    logger = setup_smoke_test_logger()
    logger.info("Testing date calculations...")
    
    try:
        from src.utils.dateutils import get_previous_month_range
        from_date, to_date, month_name = get_previous_month_range(include_z=True)
        
        if not all([from_date, to_date, month_name]):
            logger.error("Date calculation returned empty values")
            return False
            
        logger.info(f"✓ Date calculations OK (Previous month: {month_name})")
        return True
    except Exception as e:
        logger.error(f"Date calculation error: {e}")
        return False

def run_smoke_tests():
    """Run all smoke tests and return overall result"""
    logger = setup_smoke_test_logger()
    logger.info("=" * 50)
    logger.info("STARTING SMOKE TESTS")
    logger.info("=" * 50)
    
    # Load environment
    load_dotenv()
    
    tests = [
        test_environment_variables,
        test_directory_structure, 
        test_imports,
        test_date_calculations,
        test_email_service_config,
        test_zaptec_api_connection,
        test_api_structure_quick_check,  # Check for API changes
    ]
    
    passed = 0
    failed = 0
    
    try:
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
                failed += 1
    finally:
        # Clean up shared API instance
        cleanup_shared_api_instance()
    
    logger.info("=" * 50)
    logger.info(f"SMOKE TESTS COMPLETE: {passed} passed, {failed} failed")
    logger.info("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)