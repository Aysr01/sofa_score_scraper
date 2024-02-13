import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import logging


logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResultScraper:
    def __init__(self, saving_path, start_date = None, end_date = datetime.now().strftime("%Y-%m-%d")):
        self.url = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{}"
        if start_date:
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.saving_path = saving_path

    def get_json(self, desired_date):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(self.url.format(desired_date), headers=headers)
        except Exception as e:
            logger.error(f"Error while getting data! check your internet connection")
        return response.json()
    
    def get_events(self, json_data):
        events = json_data['events']
        data = []
        for event in events:
            try:
                data.append(
                    (   
                        event["startTimestamp"],
                        event["season"]["year"],
                        event["tournament"]["name"],
                        event['homeTeam']['name'],
                        event['awayTeam']['name'],
                        event['homeScore'].get('current', None),
                        event['awayScore'].get('current', None),
                        event['homeTeam']["country"].get("name", None),
                        event['awayTeam']["country"].get("name", None),
                        event["homeTeam"]["national"],
                        event["awayTeam"]["national"],
                    )
                )
            except Exception as e:
                logger.error(f"Error while extracting data: {e}")
        return data
    
    def save_to_csv(self, data, desired_date):
        df = pd.DataFrame(
            data,
            columns=[
                "startTimestamp", "year", "tournament",
                "home_team", "away_team", "home_score",
                "away_score", "home_country", "away_country",
                "is_homeTeam_national", "is_awayTeam_national"
            ]
        )
        df["home_score"] = df["home_score"].astype("Int64")
        df["away_score"] = df["away_score"].astype("Int64")
        file_path = os.path.join(self.saving_path, f"results_{desired_date}.csv")
        df.to_csv(file_path, index=False)
        logger.info(f"Data saved to {file_path}")

    def scrape_results(self):
        date = self.start_date
        if not self.start_date:
            date = self.end_date
        while date <= self.end_date:
            str_date = date.strftime("%Y-%m-%d")
            logger.info(f"Getting data for {str_date} ...")
            json_data = self.get_json(str_date)
            events = self.get_events(json_data)
            self.save_to_csv(events, str_date)
            date += timedelta(days=1)
        logger.info("Done!")

    
