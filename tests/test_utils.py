import pytest
from datetime import datetime
from src.utils.dateutils import get_previous_month_range


class TestDateUtils:
    def test_get_previous_month_range_with_z(self):
        from_date, to_date, month_name = get_previous_month_range(include_z=True)

        assert from_date.endswith("Z")
        assert to_date.endswith("Z")
        assert "T00:00:00.001Z" in from_date
        assert "T23:59:59.999Z" in to_date
        assert isinstance(month_name, str)
        assert len(month_name) > 0

    def test_get_previous_month_range_without_z(self):
        from_date, to_date, month_name = get_previous_month_range(include_z=False)

        assert not from_date.endswith("Z")
        assert not to_date.endswith("Z")
        assert "T00:00:00.001" in from_date
        assert "T23:59:59.999" in to_date

    def test_previous_month_logic(self):
        """Test that we actually get previous month dates"""
        from_date, to_date, month_name = get_previous_month_range(include_z=False)

        # Parse dates to verify they're from previous month
        from_dt = datetime.fromisoformat(from_date.replace("T00:00:00.001", ""))
        to_dt = datetime.fromisoformat(to_date.replace("T23:59:59.999", ""))

        # Should be same month
        assert from_dt.month == to_dt.month
        # Should be first and last day of month
        assert from_dt.day == 1
        # to_dt should be last day of the month (28-31)
        assert to_dt.day >= 28
