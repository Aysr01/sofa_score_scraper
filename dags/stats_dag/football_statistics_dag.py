import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.results_scraper import ResultScraper, get_events
from utils.statistics_scraper import StatsScraper
from utils.highlights_scraper import HighlightsScraper
from utils.gcs_client import GcsClient
from airflow.decorators import dag, task
from custom_operators.bq_operator import BigQueryOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.exceptions import AirflowSkipException
from datetime import datetime, timedelta
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
    execution_date = context['ds']
    gcs_client = GcsClient()
    json_data = gcs_client.is_consulted(f"results/{execution_date}.json")
    if not json_data:
        logger.info("Getting results..")
        scraper = ResultScraper()
        json_data = scraper.get_json(execution_date)
        gcs_client.upload_data(json_data, f"results/{execution_date}.json")
    return json_data


@task(task_id='extract_desired_info')
def extract_desired_info(json_data, **context):
    ds = context["ds"]
    desired_info = get_events(json_data, ds)
    context["task_instance"].xcom_push(key="desired_info", value=desired_info)


def skip_or_not(**context):
    desired_data = context['task_instance'].xcom_pull(task_ids="extract_desired_info", key="desired_info")
    if not desired_data:
        return "end"
    return "continue"

skip_or_continue = BranchPythonOperator(
    task_id='skip_or_continue',
    python_callable=skip_or_not,
)

end_ = DummyOperator(task_id='end')


continue_ = DummyOperator(task_id='continue')

def extract_stats_from_queue(ds):
    global ids_queue, matches_statistics
    stats_scraper = StatsScraper()
    gcs_client = GcsClient()
    while(True):
        try:
            match = ids_queue.get(timeout=1)
        except:
            break
        if match:
            data_path = "statistics/{}/{}.json".format(ds, match["id"])
            match_stats = gcs_client.is_consulted(data_path)
            if not match_stats:
                match_stats = stats_scraper.get_stats(match["id"])
                logger.info("Getting Data for match {}".format(match["id"]))
                if not match_stats:
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
                    return None
                gcs_client.upload_data(match_stats, data_path)
            matches_statistics.put({"statistics": match_stats, "id": match["id"]})

@task(task_id='fetch_statistics')
def fetch_statistics(**context):
    desired_data = context["task_instance"].xcom_pull(task_ids="extract_desired_info", key="desired_info")
    global ids_queue, matches_statistics
    for match in desired_data:
        ids_queue.put(match)
    # run ten Threads in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(extract_stats_from_queue, context["ds"])
    return list(matches_statistics.queue)

def extract_highlights_from_queue(ds):
    global ids_queue2, matches_highlights
    highlights_scraper = HighlightsScraper()
    gcs_client = GcsClient()
    while True:
        try:
            match = ids_queue2.get(timeout=1)
        except:
            break
        if match:
            data_path = "highlights/{}/{}.json".format(ds, match["id"])
            match_highlights = gcs_client.is_consulted(data_path)
            if not match_highlights:
                logger.info("Getting Data for match {}".format(match["id"]))
                match_highlights = highlights_scraper.get_highlights(match["id"])
                if not match_highlights:
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
                    return None 
                gcs_client.upload_data(match_highlights, data_path)
            matches_highlights.put({"highlights": match_highlights, "id": match["id"]})

@task(task_id='fetch_highlights')
def fetch_highlights(**context):
    desired_data = context["task_instance"].xcom_pull(task_ids="extract_desired_info", key="desired_info")
    global ids_queue2, matches_highlights
    for match in desired_data:
        ids_queue2.put(match)
    # run ten Threads in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(extract_highlights_from_queue, context["ds"])
    return list(matches_highlights.queue)


@task(task_id='prepare_to_load')
def prepare_to_load(matches_statistics, matches_highlights, **context):
    desired_data = context["task_instance"].xcom_pull(task_ids="extract_desired_info", key="desired_info")
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
    dag_id="football_results_dag_v2.1",
    schedule_interval='@daily',
    start_date=datetime(2022, 8, 1),
    catchup=False,
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'retries': 3,  # Number of retries for all tasks in the DAG
        'retry_delay': timedelta(minutes=1),  # Delay between retries for all tasks in the DAG
    }
)
def football_results_dag():
    #get raw data from Sofascore
    raw_data_json = get_json_data()
    # extract desired informations from matches
    desired_info = extract_desired_info(raw_data_json)
    desired_info >> skip_or_continue
    # skip or continue based on the availability of data
    skip_or_continue >> [end_, continue_]
    # fetch statistics of a specific match from Sofascore (possession, shots...etc)
    data_with_statistics = fetch_statistics()
    # fetch highlights of a specific match from Sofascore
    data_with_highlights = fetch_highlights()
    #continue if  data available
    continue_ >> [data_with_statistics, data_with_highlights]
    # merge statistics, highlights with the corresponding match data
    prepared_data = prepare_to_load(data_with_statistics, data_with_highlights)
    # load data to BigQuery
    loaded_data = load_to_bq(prepared_data)

# start the dag
football_results_dag()
