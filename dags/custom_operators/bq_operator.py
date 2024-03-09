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
        self._table = kwargs.get("table")
        self._schema = kwargs.get("schema")
        self._client = None

    def execute(self, data_dict, **context):
        """
        Returns a BigQuery PEP 249 connection object.
        """
        client = bigquery.Client()
        error = client.insert_rows_json(self._table, data_dict)
        if error != [] :
            logger.error(
                    ("Error while getting highlights for match {}-{} in {} error: {}"
                    .format(data_dict["home_team"], data_dict["away_team"], data_dict["tournament"]), error[0])
                )



if __name__ == "__main__":

    project_id = os.environ.get("GCP_PROJECT_ID")
    dataset_id = os.environ.get("BQ_DATASET_ID")
    table_id = os.environ.get("BQ_TABLE_ID")
    table = f"{project_id}.{dataset_id}.{table_id}"
    schema = [
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
    ]
    data_dict = {"name": "John", "a": 30}


    hook = BigQueryOperator(table=table, schema=schema)
    hook.execute(data_dict)