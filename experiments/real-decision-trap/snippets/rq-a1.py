import requests
from requests.adapters import HTTPAdapter
def make_session(t):
    s = requests.Session(); a = HTTPAdapter(timeout=t); s.mount("https://", a); s.mount("http://", a); return s
