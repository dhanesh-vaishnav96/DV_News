import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()


API_KEY = os.getenv("API_KEY")


def fetch_news(query):
    URL = f"https://newsapi.org/v2/everything?q={query}&apiKey={API_KEY}"
    response = requests.get(URL)
    return response.json()
