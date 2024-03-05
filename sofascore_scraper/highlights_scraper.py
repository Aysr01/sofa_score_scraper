import requests
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class HighlightsScraper():
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1/event/{}/incidents"

    def get_incidents(self, match_id):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        self.url = self.base_url.format(match_id)
        try:
            response = requests.get(self.url, headers=headers)
        except Exception as e:
            logger.error(f"Error while getting data! check your internet connection")
        return response
    
    def extract_highlights(self, data):
        highlights = {}
        for item in data.get("incidents", []):
            incident_type = item.get("incidentType")
            if incident_type == "goal":
                assist_data = item.get("assist1")
                assist = None
                if assist_data:
                    assist = {
                        "name": assist_data.get("name"),
                        "position": assist_data.get("position"),
                        "jerseyNumber": assist_data.get("jerseyNumber")
                    }

                goal = {
                    "homeScore": item.get("homeScore"),
                    "awayScore": item.get("awayScore"),
                    "time": item.get("time"),
                    "isHome": item.get("isHome"),
                    "player": {
                        "name": item["player"].get("name"),
                        "position": item["player"].get("position"),
                        "jerseyNumber": item["player"].get("jerseyNumber", None)  
                    },
                    "type": item.get("incidentClass"),
                    "assist": assist
                }
                highlights.setdefault(incident_type, []).append(goal)

            elif incident_type == "card":
                card = {
                    "time": item.get("time"),
                    "isHome": item.get("isHome"),
                    "player": {
                        "name": item["player"].get("name"),
                        "position": item["player"].get("position"),
                        "jerseyNumber": item["player"].get("jerseyNumber", None)  
                    },
                    "type": item.get("incidentClass"),
                    "rescinded": item.get("rescinded"),
                    "reason": item.get("reason")
                }
                highlights.setdefault(incident_type, []).append(card)

            elif incident_type == "substitution":
                substitution = {
                    "time": item.get("time"),
                    "isHome": item.get("isHome"),
                    "playerIn": {
                        "name": item["playerIn"].get("name"),
                        "position": item["playerIn"].get("position"),
                        "jerseyNumber": item["playerIn"].get("jerseyNumber", None)  
                    },
                    "playerOut": {
                        "name": item["playerOut"].get("name"),
                        "position": item["playerOut"].get("position"),
                        "jerseyNumber": item["playerOut"].get("jerseyNumber", None)  
                    },
                    "type": item.get("incidentClass")
                }
                highlights.setdefault(incident_type, []).append(substitution)

            elif incident_type == "penalty":
                penalty = {
                    "time": item.get("time"),
                    "isHome": item.get("isHome"),
                    "sequence": item.get("sequence"),
                    "player": {
                        "name": item["player"].get("name"),
                        "position": item["player"].get("position"),
                        "jerseyNumber": item["player"].get("jerseyNumber", None)  
                    },
                    "state": item.get("state"),
                    "reason": item.get("reason")
                }
                highlights.setdefault(incident_type, []).append(penalty)

            elif incident_type == "injuryTime":
                injury_time = {
                    "time": item.get("time"),
                    "length": item.get("length")
                }
                highlights.setdefault(incident_type, []).append(injury_time)
        return highlights
    
    def get_highlights(self, match_id):
        incidents_response = self.get_incidents(match_id)
        if incidents_response.status_code != 200:
            logger.error("Page not found, maybe the match doesn't start yet.\n"\
                         "This is the url of the last sent request: {}".format(self.url)
                         )
            return None
        incidents_json = incidents_response.json()
        extracted_highlights = self.extract_highlights(incidents_json)
        return extracted_highlights
if __name__ == "__main__":
    scraper = HighlightsScraper()
    match_id = 12049873
    with open("highlights.json", "w") as f:
        json.dump(scraper.get_highlights(match_id), f, indent=4)