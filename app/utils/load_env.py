from dotenv import load_dotenv
import os

def load_env():
    load_dotenv()
    
def get_api_key(key, default=None):
    return os.getenv(key, default)
