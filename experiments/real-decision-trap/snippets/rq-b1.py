import requests
def make_session(t):
    s = requests.Session(); s.timeout = t; return s
