from datetime import datetime, date

from config import DATE_FORMAT, DATE_FORMAT_ALT, EXP_DAYS


def parse_date(value):
    value = value.strip()
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        return datetime.strptime(value, DATE_FORMAT_ALT).date()


def format_date(value_date):
    return value_date.strftime(DATE_FORMAT)


def calc_days(loan_date):
    return (date.today() - loan_date).days


def is_expired(loan_date):
    return calc_days(loan_date) >= EXP_DAYS


def calc_duration(start_date, end_date):
    return (end_date - start_date).days
