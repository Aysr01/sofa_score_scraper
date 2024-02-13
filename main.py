from dags.sofascore_scraper.results_scraper import ResultScraper
from config import *

if __name__ == "__main__":
    result_scraper = ResultScraper(SAVING_PATH, START_DATE, END_DATE)
    result_scraper.scrape_results()
