from airflow.models.baseoperator import BaseOperator
from google.cloud import bigquery
import os
import logging


logging.basicConfig(level=logging.INFO
                    , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BigQueryOperator(BaseOperator):
    def __init__(self, **kwargs):
        self._project_id = os.environ.get("GCP_PROJECT_ID")
        self._dataset_id = os.environ.get("BQ_DATASET_ID")
        self._table_id = os.environ.get("BQ_TABLE_ID")
        self._table = f"{self._project_id}.{self._dataset_id}.{self._table_id}"
        self._client = bigquery.Client()

    def execute(self, data_dict, **context):
        error = self._client.insert_rows_json(self._table, data_dict)
        if error != [] :
            logger.error(
                    "Error while loading data of the match: " \
                    "https://www.sofascore.com/{}-{}/{}#id:{},tab:details\n" \
                    "occured errors: {}"
                    .format(
                        data_dict[0]["home_team"].lower().replace(" ", "-"),
                        data_dict[0]["away_team"].lower().replace(" ", "-"),
                        data_dict[0]["customId"],
                        data_dict[0]["id"],
                        error[0]["errors"]
                    )
                )



if __name__ == "__main__":

    project_id = os.environ.get("GCP_PROJECT_ID")
    dataset_id = os.environ.get("BQ_DATASET_ID")
    table_id = os.environ.get("BQ_TABLE_ID")
    table = f"{project_id}.{dataset_id}.{table_id}"
    data_dict = {"id": 1, "home_team": "John", "away_team": "test", "customId": 1, "boo": "boo"}


    hook = BigQueryOperator(table=table)
    hook.execute([data_dict])