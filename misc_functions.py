import datetime


def next_day(is_today: bool):
    if is_today:
        dt = datetime.datetime.now() + datetime.timedelta(seconds=1)
        while dt.isoweekday() == 7:
            dt += datetime.timedelta(days=1)
    else:
        dt = datetime.datetime.now() + datetime.timedelta(days=next_day(True) + 1, seconds=1)
        if dt.isoweekday() == 7:
            dt += datetime.timedelta(days=1)
    return (dt - datetime.datetime.now()).days
