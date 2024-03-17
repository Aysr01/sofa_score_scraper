import requests
import os
import json
import logging
from datetime import datetime, timezone
from .settings import DESIRED_COUNTRIES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResultScraper:
    def __init__(self):
        self.url = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{}"

    def get_json(self, desired_date):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(self.url.format(desired_date), headers=headers)
            json_data = response.json()
        except Exception as e:
            raise Exception(f"Error while getting data: {e}")
        return json_data

    

def get_events(json_data, execution_date):
        events = json_data['events']
        desired_data = []
        for event in events:
            try:
                event_country = event["tournament"]["category"]["name"]
                start_timestamp = datetime.fromtimestamp(event["startTimestamp"], tz=timezone.utc)
                if (event_country in DESIRED_COUNTRIES) and (start_timestamp.strftime("%Y-%m-%d") == execution_date):
                    desired_data.append(
                        {   
                            "id": event["id"],
                            "customId": event["customId"],
                            "startTimestamp": start_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "season": event["season"]["year"],
                            "country": event_country,
                            "tournament": event["tournament"]["uniqueTournament"]["name"],
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

    
