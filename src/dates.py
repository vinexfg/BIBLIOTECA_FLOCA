from datetime import datetime, date

import config


def parse_date(value):
    value = value.strip()
    try:
        return datetime.strptime(value, config.DATE_FORMAT).date()
    except ValueError:
        return datetime.strptime(value, config.DATE_FORMAT_ALT).date()


def format_date(value_date):
    return value_date.strftime(config.DATE_FORMAT)


def calc_days(loan_date):
    return (date.today() - loan_date).days


def is_expired(loan_date):
    return calc_days(loan_date) >= config.EXP_DAYS


def calc_duration(start_date, end_date):
    return (end_date - start_date).days
