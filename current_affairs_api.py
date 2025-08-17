import os
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List

logger = logging.getLogger(__name__)

class CurrentAffairsAPI:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY", "")
        self.base_url = "https://newsapi.org/v2"
        
    def get_africa_news(self, category: str = "general", limit: int = 10) -> List[Dict]:
        """Get latest Africa news"""
        if not self.news_api_key:
            return self._get_mock_africa_news()
            
        params = {
            "apiKey": self.news_api_key,
            "q": "Africa OR African Union OR ECOWAS OR SADC",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit
        }
        
        try:
            response = requests.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            return self._format_news(articles)
        except Exception as e:
            logger.error(f"Error fetching Africa news: {e}")
            return self._get_mock_africa_news()
    
    def _format_news(self, articles: List[Dict]) -> List[Dict]:
        """Format news articles for consistent output"""
        formatted = []
        for article in articles[:10]:
            formatted.append({
                "title": article.get("title", "No title"),
                "description": article.get("description", "No description"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", "Unknown")
            })
        return formatted
    
    def _get_mock_africa_news(self) -> List[Dict]:
        """Mock Africa news for development/testing"""
        return [
            {
                "title": "African Continental Free Trade Area Launches New Digital Platform",
                "description": "The AfCFTA has launched a new digital platform to facilitate cross-border trade across African nations.",
                "url": "https://example.com/afcfta-digital-platform",
                "published_at": datetime.now().isoformat(),
                "source": "African Union"
            }
        ]

# Global instance
current_affairs_api = CurrentAffairsAPI()

def get_current_affairs_api():
    return current_affairs_api
