import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.results_scraper import ResultScraper, get_events, save_to_json
from utils.statistics_scraper import StatsScraper
from utils.highlights_scraper import HighlightsScraper
from utils.settings import DESIRED_COUNTRIES
from airflow.decorators import dag, task
# from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertTableOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime
import logging
import json


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

    @task(task_id='clean_data')
    def clean_data(data):
        desired_data = []
        for match in data:
            if match["country"] in DESIRED_COUNTRIES:
                desired_data.append(match)
        return desired_data
                
    

    @task(task_id='get_statistics')
    def get_statistics(desired_data):
        stats_scraper = StatsScraper()
        matches_statistics = []
        for match in desired_data:
            match_stats = stats_scraper.get_stats(match["id"])
            if match_stats is None:
                logger.error(
                    ("Error while getting statistics for match {}-{} in {}"
                    .format(match["home_team"], match["away_team"], match["tournament"]))
                )
                match_stats = None
            else:
                matches_statistics.append({"statistics": match_stats, "id": match["id"]})
        return matches_statistics

    @task(task_id='get_highlights')
    def get_highlights(desired_data):
        highlights_scraper = HighlightsScraper()
        matches_highlights = []
        for match in desired_data:
            match_highlight = highlights_scraper.get_highlights(match["id"])
            if match_highlight is None:
                logger.error(
                    ("Error while getting highlights for match {}-{} in {}"
                    .format(match["home_team"], match["away_team"], match["tournament"]))
                )
                match_highlight = None
            else:
                matches_highlights.append({"highlights": match_highlight, "id": match["id"]})
        return matches_highlights
    
    
    @task(task_id='prepare_to_load')
    def prepare_to_load(desired_data, matches_statistics, matches_highlights, **context):
        ds = context['ds']
        kv_data = {"statistics": matches_statistics, "highlights": matches_highlights}
        for k, v in kv_data.items():
            for match_info in v:
                for match in desired_data:
                    if match_info["id"] == match["id"]:
                        match[k] = match_info
                        break
        # Save to json
        with open(f'/tmp/football_stats_{ds}.jsonl', 'w') as file:
            file.write(json.dumps(desired_data))
    
    # load_json_data = BigQueryInsertTableOperator(
    #     task_id='load_json_data',
    #     table_resource={
    #         'dataset_id': 'sofa_score',  
    #         'table_id': 'football_stats',  
    #     },
    #     create_disposition='CREATE_IF_NEEDED',
    #     write_disposition='WRITE_APPEND', 
    #     source_objects=['/tmp/football_stats_{{ ds }}.jsonl'], 
    #     source_format='NEWLINE_DELIMITED_JSON',
    #     schema_update_options=['ALLOW_FIELD_ADDITION']
    # )
            
    end = DummyOperator(task_id='end')
    
    
    data_json = get_json_data()
    events = get_events_data(data_json)
    desired_data = clean_data(events)
    data_with_statistics = get_statistics(desired_data)
    data_with_highlights = get_highlights(desired_data)
    prepared_data = prepare_to_load(desired_data, data_with_statistics, data_with_highlights)
    prepared_data >> end

football_results_dag()
