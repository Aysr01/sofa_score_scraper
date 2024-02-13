import os
# Description: Configuration file for the project

# The interval of time to scrape
# The interval is inclusive
# The format is "YYYY-MM-DD"
# if you prefer to scrape only one day, set the START_DATE and END_DATE to the same date
START_DATE = "2024-02-09"
END_DATE = "2024-02-13"


# The path to save the scraped data
SAVING_PATH = os.path.join("./")