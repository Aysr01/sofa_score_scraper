import requests
import os
import pandas as pd
from datetime import datetime, timedelta
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
        except Exception as e:
            logger.error(f"Error while getting data! check your internet connection")
        return response.json()
    

def get_events(json_data):
        events = json_data['events']
        data = []
        for event in events:
            try:
                data.append(
                    (   
                        event["id"],
                        event["startTimestamp"],
                        event["season"]["year"],
                        event["tournament"]["category"]["name"],
                        event["tournament"]["name"],
                        event.get("roundInfo", {"round": None})["round"],
                        event['homeTeam']['name'],
                        event['awayTeam']['name'],
                        event['homeScore'].get('current', None),
                        event['awayScore'].get('current', None),
                        event.get("winnerCode", None),
                        event['homeTeam']["country"].get("name", None),
                        event['awayTeam']["country"].get("name", None),
                        event["homeTeam"]["national"],
                        event["awayTeam"]["national"],
                    )
                )
            except Exception as e:
                logger.error(f"Error while extracting data: {e}")
        return data
    

def save_to_csv(data, date, saving_path):
    df = pd.DataFrame(
        data,
        columns=[
            "id", "startTimestamp", "season", "country",
            "tournament", "round", "home_team",
            "away_team", "home_score", "away_score",
            "winner_code", "home_country", "away_country",
            "is_homeTeam_national", "is_awayTeam_national"
        ]
    )
    df["home_score"] = df["home_score"].astype("Int64")
    df["away_score"] = df["away_score"].astype("Int64")
    file_path = os.path.join(saving_path, f"results_{date}.csv")
    df.to_csv(file_path, index=False)
    logger.info(f"Data saved to {file_path}")
    return file_path

    
