import requests
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class StatsScraper():

    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1/event/{}/statistics"

    def get_match_data(self, match_id):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        self.url = self.base_url.format(match_id)
        try:
            response = requests.get(self.url, headers=headers)
        except Exception as e:
            logger.error(f"Error while getting data! check your internet connection")
        return response
    
    def extract_stats(self, stats_data):
        stats = {}
        for period_data in stats_data:
            groups = period_data["groups"] 
            period_stats = {}
            for stat_group in groups:
                group_stats = {}
                for stat in stat_group["statisticsItems"]:
                    stat_name = stat["name"].lower().replace(" ", "_")
                    group_stats[stat_name] = {
                        "home": int(stat["homeValue"]),
                        "away": int(stat["awayValue"])
                    }
                    period_stats[stat_group["groupName"].lower()] = group_stats
            
            stats[period_data["period"]] = period_stats
        return stats 
    
    def get_stats(self, match_id):
        stats_response = self.get_match_data(match_id)
        if stats_response.status_code != 200:
            logger.error(
                         "Page not found, maybe the match didn't start yet.\n"\
                         "This is the url of the last sent request: {}".format(self.url)
                         )
            return None
        stats_json = stats_response.json()["statistics"]
        extracted_stats = self.extract_stats(stats_json)
        return extracted_stats
        
        



if __name__ == "__main__":
    stats_scraper = StatsScraper()
    stats_json = stats_scraper.get_stats(11907976)
    json_data = json.dump(stats_json, open("stats_data.json", "w"))