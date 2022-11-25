import datetime

# gives tomorrow unix time +5 minutes
def tomorrow_unix():
    now = datetime.datetime.now()
    today = datetime.datetime(year=now.year, month=now.month, day=now.day, minute=5)
    return (today + datetime.timedelta(days=1)).strftime("%s")
