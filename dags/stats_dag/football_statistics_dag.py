import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.results_scraper import ResultScraper, get_events, save_to_csv
from utils.statistics_scraper import StatsScraper
from utils.highlights_scraper import HighlightsScraper
from airflow.decorators import dag, task
from datetime import datetime
import logging
import pandas as pd


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


@dag(schedule_interval='@daily', start_date=datetime(2024, 2, 1), catchup=False)
def football_results_dag():

    @task(task_id='get_json_data')
    def get_json_data(**context):
        date = context['ds']
        scraper = ResultScraper()
        json_data = scraper.get_json(date)
        return json_data

    @task(task_id='get_events_data')
    def get_events_data(json_data):
        return get_events(json_data)


    @task(task_id='save_data_to_csv')
    def save_data_csv(data, **context):
        desired_date = context['ds']
        file_path = save_to_csv(data, desired_date, saving_path="./scraped_data/")
        return file_path

    @task(task_id='get_stats')
    def get_stats(file_path):
        results_df = pd.read_csv(file_path)
        for index, match in results_df.iterrows():
            match_stats = StatsScraper().get_stats(match["id"])
            return match_stats

    data_json = get_json_data()
    events = get_events_data(data_json)
    results_file_path = save_data_csv(events)
    get_stats(results_file_path)

football_results_dag()
