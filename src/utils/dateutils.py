from datetime import datetime, timedelta


def get_previous_month_range(include_z=True):
    """
    Calculates and returns the first and last day of the previous month. Also returns the month name.

    Args:
        include_z: Whether to include 'Z' timezone suffix

    Returns:
        Tuple of (from_date, to_date, prev_month_name) formatted as ISO timestamps and month name as string
    """
    today = datetime.now()
    first_of_current = today.replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    first_of_previous = last_of_previous.replace(day=1)
    prev_month_name = last_of_previous.strftime("%B")

    suffix = "Z" if include_z else ""
    from_date = first_of_previous.strftime(f"%Y-%m-%dT00:00:00.001{suffix}")
    to_date = last_of_previous.strftime(f"%Y-%m-%dT23:59:59.999{suffix}")

    return from_date, to_date, prev_month_name
