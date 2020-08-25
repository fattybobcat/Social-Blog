import datetime as dt


def year(request):
    """
    Add value with curent year
    """
    current_year = dt.datetime.today().year
    return {'year': current_year}
