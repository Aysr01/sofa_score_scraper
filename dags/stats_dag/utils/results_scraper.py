import requests
import os
import json
import logging


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
    

def get_events(json_data):
        events = json_data['events']
        data = []
        for event in events:
            try:
                data.append(
                    {   
                        "id": event["id"],
                        "startTimestamp": event["startTimestamp"],
                        "season": event["season"]["year"],
                        "country": event["tournament"]["category"]["name"],
                        "tournament": event["tournament"]["name"],
                        "round": event.get("roundInfo", {"round": None})["round"],
                        "home_team": event['homeTeam']['name'],
                        "away_team": event['awayTeam']['name'],
                        "home_score": event['homeScore'].get('current', None),
                        "away_score": event['awayScore'].get('current', None),
                        "winner_code": event.get("winnerCode", None),
                        "home_country": event['homeTeam']["country"].get("name", None),
                        "away_country": event['awayTeam']["country"].get("name", None),
                        "is_homeTeam_national": event["homeTeam"]["national"],
                        "is_awayTeam_national": event["awayTeam"]["national"],
                    }
                )
            except Exception as e:
                logger.error(f"Error while extracting data: {e}")
        return data
    

def save_to_json(data, date, saving_path):
    file_path = os.path.join(saving_path, f"results_{date}.json")
    json.dump(data, open(file_path, "w"))
    logger.info(f"Data saved to {file_path}")
    return file_path

    
