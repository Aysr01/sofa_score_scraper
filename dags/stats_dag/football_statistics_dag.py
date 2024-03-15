import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.results_scraper import ResultScraper, get_events
from utils.statistics_scraper import StatsScraper
from utils.highlights_scraper import HighlightsScraper
from airflow.decorators import dag, task
# from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertTableOperator
from airflow.operators.dummy import DummyOperator
from custom_operators.bq_operator import BigQueryOperator
from datetime import datetime
import logging
import queue
import concurrent.futures


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

ids_queue = queue.Queue()
matches_statistics = queue.Queue()

ids_queue2 = queue.Queue()
matches_highlights = queue.Queue()


@task(task_id='get_json_data')
def get_json_data(**context):
    date = context['ds']
    scraper = ResultScraper()
    json_data = scraper.get_json(date)
    return json_data


@task(task_id='extract_desired_info')
def extract_desired_info(json_data, **context):
    ds = context["ds"]
    return get_events(json_data, ds)


def extract_stats_from_queue():
    global ids_queue, matches_statistics
    stats_scraper = StatsScraper()
    while(True):
        try:
            match = ids_queue.get(timeout=1)
        except:
            break
        if match:
            match_stats = stats_scraper.get_stats(match["id"])
            if match_stats is None:
                logger.error(
                    "Error while getting statistics of the match: " \
                    "https://www.sofascore.com/{}-{}/{}#id:{},tab:details" \
                    .format(
                        match["home_team"].lower().replace(" ", "-"),
                        match["away_team"].lower().replace(" ", "-"),
                        match["customId"],
                        match["id"]
                    )
                )
            else:
                matches_statistics.put({"statistics": match_stats, "id": match["id"]})

@task(task_id='fetch_statistics')
def fetch_statistics(desired_data):
    global ids_queue, matches_statistics
    for match in desired_data:
        ids_queue.put(match)
    # run ten Threads in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(extract_stats_from_queue)
    return list(matches_statistics.queue)

def extract_highlights_from_queue():
    global ids_queue2, matches_highlights
    highlights_scraper = HighlightsScraper()
    while True:
        try:
            match = ids_queue2.get(timeout=1)
        except:
            break
        if match:
            match_highlights = highlights_scraper.get_highlights(match["id"])
            if match_highlights is None:
                logger.error(
                    "Error while getting highlights of the match: " \
                    "https://www.sofascore.com/{}-{}/{}#id:{},tab:details" \
                    .format(
                        match["home_team"].lower().replace(" ", "-"),
                        match["away_team"].lower().replace(" ", "-"),
                        match["customId"],
                        match["id"]
                    )
                )
            else:
                matches_highlights.put({"highlights": match_highlights, "id": match["id"]})

@task(task_id='fetch_highlights')
def fetch_highlights(desired_data):
    global ids_queue2, matches_highlights
    for match in desired_data:
        ids_queue2.put(match)
    # run ten Threads in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(extract_highlights_from_queue)
    return list(matches_highlights.queue)


@task(task_id='prepare_to_load')
def prepare_to_load(desired_data, matches_statistics, matches_highlights):
    kv_data = {"statistics": matches_statistics, "highlights": matches_highlights}
    for k, v in kv_data.items():
        for match_info in v:
            for match in desired_data:
                if match_info["id"] == match["id"]:
                    match[k] = match_info[k]
                    break
    return desired_data


@task(task_id='load_to_bq')
def load_to_bq(prepared_data):
    bq_client = BigQueryOperator()
    for data in prepared_data:
        bq_client.execute([data])


@dag(
        dag_id="football_results_dag_v2.0", schedule_interval='@daily',
        start_date=datetime(2024, 2, 1), catchup=False,
)
def football_results_dag():

    start = DummyOperator(task_id='start')

    end = DummyOperator(task_id='end')
    
    raw_data_json = get_json_data()
    desired_info = extract_desired_info(raw_data_json)
    data_with_statistics = fetch_statistics(desired_info)
    data_with_highlights = fetch_highlights(desired_info)
    prepared_data = prepare_to_load(desired_info, data_with_statistics, data_with_highlights)
    loaded_data = load_to_bq(prepared_data)
    start >> raw_data_json
    loaded_data >> end

football_results_dag()
