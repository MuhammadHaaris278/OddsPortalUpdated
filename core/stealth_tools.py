# core/stealth_tools.py

from utils.proxy_pool import get_random_proxy
from utils.user_agent_pool import get_random_user_agent

def get_stealth_config():
    return {
        "proxy": get_random_proxy(),
        "user_agent": get_random_user_agent()
    }
 