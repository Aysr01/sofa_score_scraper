import unittest
import json
from utils.highlights_scraper import HighlightsScraper

class TestHighlightsScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = HighlightsScraper()
        self.data = {
            "incidents": [
                {
                    "text": "PEN",
                    "homeScore": 4,
                    "awayScore": 2,
                    "isLive": False,
                    "time": 999,
                    "addedTime": 999,
                    "reversedPeriodTime": 7,
                    "incidentType": "period"
                },
                {
                    "player": {
                        "name": "Gonzalo Montiel",
                        "slug": "gonzalo-montiel",
                        "shortName": "G. Montiel",
                        "position": "D",
                        "jerseyNumber": "29",
                        "userCount": 6835,
                        "id": 822933,
                        "fieldTranslations": {
                            "nameTranslation": {
                                "ar": "\u062c\u0648\u0646\u0632\u0627\u0644\u0648 \u0645\u0648\u0646\u062a\u064a\u0644"
                            },
                            "shortNameTranslation": {
                                "ar": "\u062c. \u0645\u0648\u0646\u062a\u064a\u0644"
                            }
                        }
                    },
                    "homeScore": 4,
                    "awayScore": 2,
                    "sequence": 8,
                    "description": "Scored",
                    "id": 118412937,
                    "incidentType": "penaltyShootout",
                    "isHome": True,
                    "incidentClass": "scored",
                    "reason": "scored"
                }
            ]
        }

    def test_extract_highlights(self):
        expected_highlights = {
            'penaltyShootout': [
                {
                    'player': {
                        'name': 'Gonzalo Montiel',
                        'position': 'D',
                        'jerseyNumber': '29'
                    },
                    "homeScore": 4,
                    "awayScore": 2,
                    "sequence": 8,
                    "isHome": True,
                    "type" : "scored",
                    "reason": "scored"
                }
            ]
        }
        highlights = self.scraper.extract_highlights(self.data)
        self.assertEqual(dict(highlights), expected_highlights)

if __name__ == '__main__':
    unittest.main()