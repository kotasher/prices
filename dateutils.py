import datetime


# if used with MSK timezone, it is 06:00 MSK
def tomorrow_unix_moex():
    now = datetime.datetime.now(datetime.timezone.utc)
    now = now.replace(minute=0, hour=6, second=0, microsecond=0)
    return (now + datetime.timedelta(days=1)).strftime("%s")
