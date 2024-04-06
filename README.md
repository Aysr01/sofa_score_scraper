## 1- Introduction
The Sofascore scraper is an ETL (Extract, Transform, Load) system that retrieves data from the Sofascore website [Sofascore](https://www.sofascore.com/). This scraper can extract information about any match at a specified date or over a date range.

The key data collected by the scraper includes:

- Match-level information: start time, tournament, match score, round, season, etc.
- Team-level information such as names of the teams and their countries.
- Match statistics, such as: possession, and number of shots on target.
- Timeline of the most important events that occurred during the match.

All the scraped fields are contained in [schema.json](https://github.com/Aysr01/sofa_score_scraper/blob/master/schema.json) file
that represents the schema of BQ table.



### **Used Technologies:**
- Docker
- Airflow
- Python(json, requests, BigQuery and Cloud Storage clients)
- Cloud computing(BigQuery, GCS, Cloud Composer, cloud loggs to analyse logs)

## 2- Run the ETL System

### 2.1- Create GCS Bucket
On Google Cloud Platform (GCP), you should create a Cloud Storage bucket with a name of your choice.
This bucket will be used to store the data retrieved from the Sofascore website. By storing the retrieved data in Cloud Storage,
you can use it as a checkpoint during the execution of your data processing job. This means that instead of having to resend requests to Sofascore (which may be limited),
you can resume the data processing from the checkpoint stored in Cloud Storage. Storing the data in Cloud Storage also provides more flexibility,
as you can change the way you process the data in the future without having to re-fetch the data from Sofascore, as it will be available in the Cloud Storage bucket.

### 2.2- Create a BQ Table
Create a BQ Dataset and Table, when defining the schema for the table, use the schema provided in the file [schema.json](https://github.com/Aysr01/sofa_score_scraper/blob/master/schema.json).
Also, you should partition data on "startTimestamp" field (it's recommended to partition by year to avoid surpassing the partitioning limit in BQ). For the clustering,
Choose 4 fields from the schema that you think would be most useful for clustering the data, based on your anticipated analysis requirements.

By partitioning the data by year on the "startTimestamp" field and clustering the table on 4 relevant fields, you can optimize the performance and efficiency of your BigQuery-based data processing and analysis.

### 2.3- Create a Service Account and Grant it the necessary permissions
Create a [service account](https://cloud.google.com/iam/docs/service-account-overview) and grant it access to write and read from the created bucket and also to edit the created BigQuery table.
After creating the service account, generate a [service account key](https://www.youtube.com/watch?v=dj9fxiuz4WM&ab_channel=M2MSupportInc) and download it in JSON format. In the project folder, create a "credentials" folder, then move the downloaded file to it, and rename the file to "credentials.json".

### 2.4- Add a list of proxies
If you plan to scrape a large volume of data from Sofascore, you will need to use a list of proxies to bypass the Sofascore requests limit. To do this, you will need to override the content of the "valid_proxies.txt" file in the proxies folder with your own list of valid proxies.
This will allow your ETL system to rotate through the proxies and avoid hitting the Sofascore request limit.

Make sure to thoroughly test the proxies to ensure they are working correctly before running your large-scale data scraping. Regularly updating and validating the proxy list will be important to maintain the efficiency and reliability of your ETL pipeline.

### 2.5- Configure Tournament Selection
In the file `dags/stats_dag/utils/settings.py`, set the `DESIRED_TOURNAMENT` variable to specify the tournament you want to fetch data for.
If you want to scrape data for all the leagues across the world, set the `DESIRED_TOURNAMENT` variable to "ALL".

NB: you should write league names as they are in Sofascore.

![image](https://github.com/Aysr01/sofa_score_scraper/assets/114707989/f7921ceb-e204-4ba1-91ba-1776a6a9da9b)

### 2.6- Configure Docker Compose file
In the "docker-compose.yml" file and precisely in the webserver and scheduler services, change the following environment variables with the configurations that
you set while creating the GCS bucket and BQ table.

![image](https://github.com/Aysr01/sofa_score_scraper/assets/114707989/6088d765-da73-461c-87c0-fd1e68a66fb4)

### 2.7- Run containers
In your terminal run the following command to start the etl system `docker-compose up`.

after running the containers a job of the last day will start. the dag is scheduled to be triggered daily at `00:00` at your local time.

if you aspire to scrape a range of dates run the following command in the scheduler container:

  `airflow dags backfill football_results_dag_v2.1 -s <start_date> -e <end_date>`.

### 2.8- Deploy the Dag on Cloud Composer (Optional)
The scraping process for the Sofascore data may take a while to complete. To ensure reliable and efficient execution, it is recommended to run the Sofascore scraper DAG (Directed Acyclic Graph) in Google Cloud Composer, a managed Apache Airflow service on Google Cloud Platform.

## 3- ETL Architecture

<center><img src="https://github.com/Aysr01/sofa_score_scraper/assets/114707989/1dae50db-318b-44a8-a901-9de7d1261ce3" width="800" /></center>

## 4- Dag Overview
The core tasks in our dag are:

![image](https://github.com/Aysr01/sofa_score_scraper/assets/114707989/24c7aa2c-f2b2-4501-b14c-ad3da6b0d79a)

- **get_json_data:** This task retrieves data from Sofascore.
- **extract_desired_info:** This task filters the fetched data based on the set settings.
- **skip_or_continue:** This task  decides whether to continue or skip the process if there is no match in the execution date.
- **end_OperatorTask:** This task represents the end of the workflow.
- **continue:** Resume the workflow.
- **fetch_statistics:** This task fetches statistics of a specific match.
- **fetch_highlights:** This task fetches the timeline of important events in a specific match.
- **prepare_to_load:** This task prepares the data for loading into BigQuery.
- **load_to_bq:** This task loads the data into a BigQuery (BQ) table.
