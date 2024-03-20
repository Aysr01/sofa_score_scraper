import requests
import os
import json
import logging
from datetime import datetime, timezone
import random
from .settings import DESIRED_TOURNAMENTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResultScraper:
    def __init__(self):
        self.url = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{}"
        with open(os.environ.get("PROXIES_PATH"), "r") as f: 
            self.proxies = f.read().split("\n")

    def get_json(self, desired_date):
        headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
        while True:
            try:
                proxy = random.choice(self.proxies)
                response = requests.get(self.url.format(desired_date), headers=headers, proxies={'http': f"http://{proxy}="})
                if response.status_code == 200:
                    logger.info(f"scraped data using proxy: {proxy}")
                    json_data = response.json()
                    break
                if response.status_code == 404:
                    logger.error(f"Page not found! the url in question is: {self.url.format(desired_date)}")
                    return None
            except Exception as e:
                logger.error(f"the following proxy failed: {proxy}")
                json_data = None 
        return json_data

    

def get_events(json_data, execution_date):
        events = json_data['events']
        desired_data = []
        for event in events:
            try:
                tournament = event["tournament"]["uniqueTournament"]["name"] 
                country = event["tournament"]["category"]["name"]
                start_timestamp = datetime.fromtimestamp(event["startTimestamp"], tz=timezone.utc)
                if ((tournament, country) in DESIRED_TOURNAMENTS) and (start_timestamp.strftime("%Y-%m-%d") == execution_date):
                    desired_data.append(
                        {   
                            "id": event["id"],
                            "customId": event["customId"],
                            "startTimestamp": start_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "season": event["season"]["year"],
                            "country": country,
                            "tournament": tournament,
                            "round": event["roundInfo"]["round"],
                            "home_team": event['homeTeam']['name'],
                            "away_team": event['awayTeam']['name'],
                            "status": event["status"]["type"],
                            "home_score": event['homeScore'].get('current', None),
                            "away_score": event['awayScore'].get('current', None),
                            "winner_code": event.get("winnerCode", None),
                            "home_country": event['homeTeam']["country"].get("name", None),
                            "away_country": event['awayTeam']["country"].get("name", None),
                            "is_homeTeam_national": event["homeTeam"]["national"],
                            "is_awayTeam_national": event["awayTeam"]["national"],
                        }
                    )
            except KeyError as e:
                logger.error(f"Error while extracting data for event: {event}")
                logger.error(f"KeyError: {e}")
            except Exception as e:
                logger.error(f"Error while extracting data for event: {event}")
                logger.error(f"Unexpected error: {e}")
        return desired_data
    

def save_to_json(data, date, saving_path):
    if not os.path.exists(saving_path):
        os.makedirs(saving_path)
    file_path = os.path.join(saving_path, f"results_{date}.json")
    json.dump(data, open(file_path, "w"))
    logger.info(f"Data saved to {file_path}")
    return file_path

    
