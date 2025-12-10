import pytest
from src.api.zaptec_api import ZaptecApi
from src.utils.dateutils import get_previous_month_range

class TestAPIFieldMapping:
    """
    Tests that verify the exact field names and data access patterns 
    used in the business logic haven't changed.
    """
    
    @pytest.mark.integration
    def test_invoicing_report_field_access(self):
        """Test that all field access patterns used in InvoicingReport still work"""
        from_date, to_date, _ = get_previous_month_range(include_z=True)
        
        with ZaptecApi() as api:
            sessions = api.get_charging_sessions(from_date, to_date)
            
            if len(sessions.Data) > 0:
                session = sessions.Data[0]
                
                # These are the EXACT field accesses from invoicing_report.py process_charging_data()
                try:
                    user_email = session.UserEmail  # Line 89: session.UserEmail
                    user_name = session.UserFullName  # Line 90: session.UserFullName  
                    user_id = session.UserId  # Line 91: session.UserId
                    device_name = session.DeviceName  # Line 92: session.DeviceName
                    energy = session.Energy  # Line 93: session.Energy
                    start_time = session.StartDateTime  # Line 94: session.StartDateTime
                    end_time = session.EndDateTime  # Line 94: session.EndDateTime
                    
                    # Verify these can be used in business logic
                    assert isinstance(user_email, str) and '@' in user_email, "UserEmail should be valid email"
                    assert isinstance(user_name, str) and len(user_name) > 0, "UserFullName should be non-empty string"
                    assert isinstance(energy, (int, float)) and energy >= 0, "Energy should be non-negative number"
                    assert device_name.startswith('Plats '), f"DeviceName format changed: {device_name}"
                    
                except AttributeError as e:
                    pytest.fail(f"BREAKING CHANGE: Field access failed - {e}. This will break InvoicingReport!")

    @pytest.mark.integration  
    def test_monthly_summary_field_access(self):
        """Test that all field access patterns used in MonthlySummaryReport still work"""
        from_date, to_date, _ = get_previous_month_range(include_z=False)
        
        with ZaptecApi() as api:
            report = api.get_installation_report(from_date, to_date)
            
            if len(report.totalUserChargerReportModel) > 0:
                user_report = report.totalUserChargerReportModel[0]
                
                # These are the EXACT field accesses from monthly_summary_report.py generate_summary_report()
                try:
                    group_name = user_report.GroupAsString  # Line 49: report.GroupAsString
                    user_details = user_report.UserDetails  # Line 50: report.UserDetails
                    energy = user_report.TotalChargeSessionEnergy  # Line 51: report.TotalChargeSessionEnergy
                    duration = user_report.TotalChargeSessionDuration  # Line 52: report.TotalChargeSessionDuration  
                    sessions = user_report.TotalChargeSessionCount  # Line 55: report.TotalChargeSessionCount
                    
                    # Test UserDetails access pattern
                    if user_details:
                        email = user_details.Email  # Line 50: report.UserDetails.Email
                        full_name = user_details.FullName  # Used for user identification
                        
                        assert isinstance(email, str), "UserDetails.Email should be string"
                        assert isinstance(full_name, str), "UserDetails.FullName should be string"
                    
                    # Verify data types match business logic expectations
                    assert isinstance(group_name, str), "GroupAsString should be string"
                    assert isinstance(energy, (int, float)), "TotalChargeSessionEnergy should be numeric"
                    assert isinstance(duration, (int, float)), "TotalChargeSessionDuration should be numeric"
                    assert isinstance(sessions, int), "TotalChargeSessionCount should be integer"
                    
                except AttributeError as e:
                    pytest.fail(f"BREAKING CHANGE: Field access failed - {e}. This will break MonthlySummaryReport!")

    @pytest.mark.integration
    def test_device_name_format_consistency(self):
        """Test that DeviceName format is still 'Plats XX' as expected by _format_objekt_id()"""
        from_date, to_date, _ = get_previous_month_range(include_z=True)
        
        with ZaptecApi() as api:
            sessions = api.get_charging_sessions(from_date, to_date)
            
            device_names = [session.DeviceName for session in sessions.Data]
            unique_names = set(device_names)
            
            for device_name in unique_names:
                # This format is critical for _format_objekt_id() in invoicing_report.py
                assert device_name.startswith('Plats '), f"DeviceName format changed: '{device_name}' (expected 'Plats XX')"
                
                # Verify we can extract number as expected
                try:
                    number_part = device_name.split()[1]  # Line 195: device_name.split()[1]
                    int(number_part)  # Should be convertible to int
                except (IndexError, ValueError):
                    pytest.fail(f"DeviceName format incompatible with business logic: '{device_name}'")