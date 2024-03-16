"""
Operators to retrieve and upload data into bigquery

"""
import os
from google.cloud import storage
import json
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class GcsClient():
    def __init__(self):
        self.bucket_name = os.environ["BUCKET_ID"]
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
        if not self.bucket.exists():
            logger.critical("Bucket not found, creating a new one...")
            bucket = storage.Bucket(self.client, name=self.bucket_name)
            bucket.versioning_enabled = True
            bucket.create()
            logger.info("Bucket create successfully")

    def upload_data(self, content, destination):
        blob = self.bucket.blob(destination)
        try:
            blob.upload_from_string(json.dumps(content))
        except FileNotFoundError as e:
            logging.error(f"File Not Found: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def read_file(self, source_file):
        blob = self.bucket.blob(source_file)
        try:
            binary_data = blob.download_as_bytes()
            data_json = json.loads(binary_data.decode("utf-8"))
            return data_json
        except Exception as e:
            logger.error(f"Error occured while downloading file {source_file}: {e}")
    
    def is_consulted(self, source_file):
        """
        This method verify if the desired data is already fetched from
        Sofascore. If it's the case, it download the data in question from
        GCS.      
        """
        blob = self.bucket.blob(source_file)
        if blob.exists():
            return self.read_file(source_file)

        



if __name__ == "__main__":
    gcs_client = GcsClient()
    gcs_client.upload_data({"hello world": 22}, "test.json")




