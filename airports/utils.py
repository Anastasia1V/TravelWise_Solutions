# airports/utils.py
import requests

def fetch_airport_info(icao_code):
    url = f"https://avwx.rest/api/airport/{icao_code}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            'name': data['name'],
            'city': data['city'],
            'country': data['country']
        }
    return None