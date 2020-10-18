import datetime as dt


def year(request):
    """Function for getting current year"""
    year = dt.datetime.now().year
    return {'year': year, }
