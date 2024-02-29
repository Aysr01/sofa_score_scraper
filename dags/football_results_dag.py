from airflow.decorators import dag, task
from datetime import datetime
import logging
import requests
import pandas as pd
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

@dag(schedule_interval='@daily', start_date=datetime(2024, 2, 1), catchup=True)
def football_results_dag():

    @task(task_id='get_json_data')
    def get_json(**context):
        desired_date = context['ds']
        url = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{}".format(desired_date)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(url.format(desired_date), headers=headers)
        except Exception as e:
            logger.error(f"Error while getting data! check your internet connection")
        return response.json()

    @task(task_id='get_events')
    def get_events(json_data):
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

    @task(task_id='save_to_csv')
    def save_to_csv(data, **context):
        desired_date = context['ds']
        saving_path = "/opt/airflow/scraped_data"
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
        file_path = os.path.join(saving_path, f"results_{desired_date}.csv")
        df.to_csv(file_path, index=False)
        logger.info(f"Data saved to {file_path}")
        return file_path
    
    data_json = get_json()
    events = get_events(data_json)
    save_to_csv(events)

football_results_dag()
