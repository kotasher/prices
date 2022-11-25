import datetime


def tomorrow():
    return datetime.date.today() + datetime.timedelta(days=1)


def tomorrow_unix():
    return tomorrow().strftime("%s")
