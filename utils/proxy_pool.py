# utils/proxy_pool.py

import random

# Sample free proxies (rotate often or expand from proxy list APIs)
FREE_PROXIES = [
    "http://190.61.88.147:8080",
    "http://138.128.91.65:8000",
    "http://51.81.82.175:3128",
    "http://103.167.68.25:8080",
    "http://64.225.8.132:9981"
]

def get_random_proxy():
    return random.choice(FREE_PROXIES)
