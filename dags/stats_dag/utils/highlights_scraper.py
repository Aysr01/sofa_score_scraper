import requests
import logging
import json
from collections import defaultdict
from typing import Dict, Union, Optional
import os
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class HighlightsScraper():
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1/event/{}/incidents"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        with open(os.environ.get("PROXIES_PATH"), "r") as f: 
            self.proxies = f.read().split("\n")

    def get_incidents(self, match_id: int) -> Optional[requests.Response]:
        self.url = self.base_url.format(match_id)
        try:
            while True:
                proxy = random.choice(self.proxies)
                response = requests.get(self.url, headers=self.headers, proxies={'http': f"http://{proxy}="})
                if response.status_code == 200:
                    logger.info(f"scraped data using proxy: {proxy}")
                    break
            response = requests.get(self.url, headers=self.headers)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while getting data! {e}")
            response = None  
        return response

    def extract_highlights(self, data: Dict) -> Dict[str, list]:
        highlights: Dict[str, list] = defaultdict(list)
        try:
            _data = data["incidents"]
        except KeyError:
            logger.error("There is no data to extract highlights from! Maybe the match doesn't start yet.")
            return None  

        for item in _data:
            try:
                incident_type = item["incidentType"]
            except KeyError:
                logger.error(f"Error while extracting incident type from data: {item}")
                continue

            if incident_type == "goal":
                try:
                    assist_data = item.get("assist1")
                    assist = {k: v for k, v in assist_data.items() if k in ["name", "position", "jerseyNumber"]} if assist_data else None
                    player_data = item.get("player")
                    player = {k: v for k, v in player_data.items() if k in ["name", "position", "jerseyNumber"]} if player_data else None
                except KeyError:
                    logger.error(f"Error while extracting player or assist data from goal: {item}")
                    continue

                goal = {
                    "homeScore": item.get("homeScore"),
                    "awayScore": item.get("awayScore"),
                    "time": item.get("time", None),
                    "isHome": item.get("isHome", None),
                    "player": player,
                    "type": item.get("incidentClass"),
                    "assist": assist
                }
                highlights[incident_type].append(goal)

            elif incident_type == "card":
                try:
                    player_data = item.get("player")
                    player = {k: v for k, v in player_data.items() if k in ["name", "position", "jerseyNumber"]} if player_data else None
                except KeyError:
                    logger.error(f"Error while extracting player data from card: {item}")
                    continue

                card = {
                    "time": item.get("time", None),
                    "isHome": item.get("isHome"),
                    "player": player,
                    "type": item.get("incidentClass"),
                    "rescinded": item.get("rescinded", None),
                    "reason": item.get("reason", None)
                }
                highlights[incident_type].append(card)

            elif incident_type == "substitution":
                try:
                    playerIn_data = item.get("playerIn")
                    playerIn = {k: v for k, v in playerIn_data.items() if k in ["name", "position", "jerseyNumber"]} if playerIn_data else None
                    playerOut_data = item.get("playerOut")
                    playerOut = {k: v for k, v in playerOut_data.items() if k in ["name", "position", "jerseyNumber"]} if playerOut_data else None
                except KeyError:
                    logger.error(f"Error while extracting playerIn or playerOut data from substitution: {item}")
                    continue

                substitution = {
                    "time": item.get("time"),
                    "isHome": item.get("isHome"),
                    "playerIn": playerIn,
                    "playerOut": playerOut,
                    "type": item.get("incidentClass")
                }
                highlights[incident_type].append(substitution)

            elif incident_type == "penalty":
                try:
                    player_data = item.get("player")
                    player = {k: v for k, v in player_data.items() if k in ["name", "position", "jerseyNumber"]} if player_data else None
                except KeyError:
                    logger.error(f"Error while extracting player data from penalty: {item}")
                    continue

                penalty = {
                    "time": item.get("time", None),
                    "isHome": item.get("isHome"),
                    "sequence": item.get("sequence", None),
                    "player": player,
                    "state": item.get("state", None),
                    "reason": item.get("reason", None)
                }
                highlights[incident_type].append(penalty)

            elif incident_type == "injuryTime":
                injury_time = {
                    "time": item.get("time", None),
                    "length": item.get("length", None)
                }
                highlights[incident_type].append(injury_time)

        return highlights

    def get_highlights(self, match_id: int) -> Dict[str, list]:
        incidents_response = self.get_incidents(match_id)
        if incidents_response is None or incidents_response.status_code != 200:
            logger.error(
                "Page not found, maybe the match doesn't start yet"
            )
            return {} 

        try:
            incidents_json = incidents_response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Error while decoding JSON response: {e}")
            incidents_json = {} 
        extracted_highlights = self.extract_highlights(incidents_json)
        return extracted_highlights

if __name__ == "__main__":
    scraper = HighlightsScraper()
    match_id = 11367973
    with open("highlights.json", "w") as f:
        json.dump(scraper.get_highlights(match_id), f, indent=4)