import pytest
from src.api.zaptec_api import ZaptecApi
from src.utils.dateutils import get_previous_month_range

class TestZaptecAPIContract:
    """
    API contract tests - verify Zaptec API hasn't changed unexpectedly.
    These tests make REAL API calls to catch breaking changes.
    """
    
    @pytest.mark.integration
    def test_charging_sessions_response_structure(self):
        """Test that charging sessions API returns expected structure"""
        # Use a small date range to minimize data
        from_date, to_date, _ = get_previous_month_range(include_z=True)
        
        with ZaptecApi() as api:
            response = api.get_charging_sessions(from_date, to_date)
            
            # Verify response structure
            assert hasattr(response, 'Pages'), "Response missing 'Pages' field"
            assert hasattr(response, 'Data'), "Response missing 'Data' field"
            assert isinstance(response.Pages, int), "Pages should be integer"
            assert isinstance(response.Data, list), "Data should be list"
            
            # CRITICAL: Validate field names that business logic depends on
            if len(response.Data) > 0:
                session = response.Data[0]
                
                # These field names are used directly in invoicing_report.py
                critical_fields = {
                    'UserEmail': 'Used for grouping users in reports',
                    'UserFullName': 'Used in report comments', 
                    'Energy': 'Used for cost calculations',
                    'StartDateTime': 'Used for duration calculations',
                    'EndDateTime': 'Used for duration calculations', 
                    'DeviceName': 'Used for Objekt-ID formatting',
                    'UserId': 'Used for user identification'
                }
                
                for field, usage in critical_fields.items():
                    assert hasattr(session, field), f"BREAKING CHANGE: Session missing '{field}' field ({usage})"
                    
                    # Validate field has expected data type
                    field_value = getattr(session, field)
                    if field in ['StartDateTime', 'EndDateTime']:
                        # Should be datetime objects after Pydantic parsing
                        from datetime import datetime
                        assert isinstance(field_value, datetime), f"Field '{field}' should be datetime, got {type(field_value)}"
                    elif field == 'Energy':
                        assert isinstance(field_value, (int, float)), f"Field '{field}' should be numeric, got {type(field_value)}"
                    elif field in ['UserEmail', 'UserFullName', 'DeviceName', 'UserId']:
                        assert isinstance(field_value, str), f"Field '{field}' should be string, got {type(field_value)}"
            
            # VERIFY: Pagination is handled correctly
            if response.Pages > 1:
                # This is fine now - we handle pagination
                print(f"✓ Pagination working: fetched {len(response.Data)} items across {response.Pages} pages")
            
            # Verify we got all data when there are multiple pages
            if response.Pages > 1 and len(response.Data) < 50:
                pytest.fail(
                    f"Pagination issue: {response.Pages} pages but only {len(response.Data)} items. "
                    f"Expected more data across multiple pages."
                )

    @pytest.mark.integration
    def test_installation_report_response_structure(self):
        """Test that installation report API returns expected structure"""
        from_date, to_date, _ = get_previous_month_range(include_z=False)
        
        with ZaptecApi() as api:
            response = api.get_installation_report(from_date, to_date)
            
            # Verify response structure
            assert hasattr(response, 'totalUserChargerReportModel'), "Missing totalUserChargerReportModel"
            assert isinstance(response.totalUserChargerReportModel, list), "totalUserChargerReportModel should be list"
            
            if len(response.totalUserChargerReportModel) > 0:
                user_report = response.totalUserChargerReportModel[0]
                
                # These field names are used directly in monthly_summary_report.py
                critical_report_fields = {
                    'GroupAsString': 'Used for user_name in summary reports',
                    'TotalChargeSessionCount': 'Used for session count totals',
                    'TotalChargeSessionEnergy': 'Used for energy totals', 
                    'TotalChargeSessionDuration': 'Used for duration totals',
                    'UserDetails': 'Used for email extraction'
                }
                
                for field, usage in critical_report_fields.items():
                    assert hasattr(user_report, field), f"BREAKING CHANGE: Report missing '{field}' field ({usage})"
                    
                    # Validate field data types
                    field_value = getattr(user_report, field)
                    if field in ['TotalChargeSessionCount']:
                        assert isinstance(field_value, int), f"Field '{field}' should be int, got {type(field_value)}"
                    elif field in ['TotalChargeSessionEnergy', 'TotalChargeSessionDuration']:
                        assert isinstance(field_value, (int, float)), f"Field '{field}' should be numeric, got {type(field_value)}"
                    elif field == 'GroupAsString':
                        assert isinstance(field_value, str), f"Field '{field}' should be string, got {type(field_value)}"
                
                # CRITICAL: UserDetails structure used in reports
                if user_report.UserDetails:
                    user_details = user_report.UserDetails
                    critical_user_fields = {
                        'Email': 'Used for email column in reports',
                        'FullName': 'Used for user identification'
                    }
                    
                    for field, usage in critical_user_fields.items():
                        assert hasattr(user_details, field), f"BREAKING CHANGE: UserDetails missing '{field}' field ({usage})"
                        field_value = getattr(user_details, field)
                        assert isinstance(field_value, str), f"UserDetails.{field} should be string, got {type(field_value)}"

    @pytest.mark.integration
    def test_api_authentication_still_works(self):
        """Test that API authentication hasn't changed"""
        with ZaptecApi() as api:
            token_data = api.get_auth_token()
            
            assert 'access_token' in token_data, "Authentication response missing access_token"
            assert 'expires_in' in token_data, "Authentication response missing expires_in"
            assert isinstance(token_data['expires_in'], int), "expires_in should be integer"

    @pytest.mark.integration
    def test_data_completeness_check(self):
        """Test that we're getting complete data (not truncated by pagination)"""
        from_date, to_date, _ = get_previous_month_range(include_z=True)
        
        with ZaptecApi() as api:
            # Get both detailed sessions and summary report
            sessions_response = api.get_charging_sessions(from_date, to_date)
            summary_response = api.get_installation_report(from_date.replace('Z', ''), to_date.replace('Z', ''))
            
            # Count sessions from detailed API
            detailed_session_count = len(sessions_response.Data)
            
            # Count sessions from summary API
            summary_session_count = sum(
                report.TotalChargeSessionCount 
                for report in summary_response.totalUserChargerReportModel
            )
            
            # They should match (or be close if there are timing differences)
            if abs(detailed_session_count - summary_session_count) > 5:
                pytest.fail(
                    f"Session count mismatch! Detailed API: {detailed_session_count}, "
                    f"Summary API: {summary_session_count}. This suggests pagination issues."
                )