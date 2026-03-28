import requests
import os
from dotenv import load_dotenv
load_dotenv()
url = 'https://www.alphavantage.co/query?function=EARNINGS&symbol=IBM&apikey=demo'
r = requests.get(url)
data = r.json()

print(data)
