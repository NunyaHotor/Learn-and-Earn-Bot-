import requests
import logging
from datetime import datetime, timedelta
import threading
import time

logger = logging.getLogger(__name__)

class ExchangeRateService:
    def __init__(self):
        self.base_currency = 'USD'
        self.target_currency = 'GHS'
        self.rate = 11.8  # Default rate
        self.last_updated = datetime.now()
        self.update_interval = timedelta(hours=6)
        
    def fetch_exchange_rate(self):
        """Fetch the latest USD to GHS exchange rate from API"""
        try:
            # Using multiple APIs for redundancy
            apis = [
                f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}",
                f"https://open.er-api.com/v6/latest/{self.base_currency}",
                f"https://api.exchangerate.host/latest?base={self.base_currency}"
            ]
            
            for api_url in apis:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'rates' in data and self.target_currency in data['rates']:
                            rate = data['rates'][self.target_currency]
                            logger.info(f"Updated exchange rate: 1 USD = {rate} GHS")
                            return rate
                except Exception as e:
                    logger.warning(f"Failed to fetch from {api_url}: {e}")
                    continue
                    
            return self.rate  # Return current rate if all APIs fail
        except Exception as e:
            logger.error(f"Error fetching exchange rate: {e}")
            return self.rate
            
    def update_rate(self):
        """Update the exchange rate"""
        new_rate = self.fetch_exchange_rate()
        if new_rate != self.rate:
            self.rate = new_rate
            self.last_updated = datetime.now()
            logger.info(f"Exchange rate updated to {new_rate}")
            
    def should_update(self):
        """Check if rate should be updated"""
        return datetime.now() - self.last_updated > self.update_interval
        
    def get_rate(self):
        """Get current exchange rate"""
        if self.should_update():
            self.update_rate()
        return self.rate
        
    def get_rate_for_currency(self, currency_code):
        """Get rate for specific currency"""
        try:
            response = requests.get(f"https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['rates'].get(currency_code, 1.0)
        except:
            return 1.0

exchange_rate_service = ExchangeRateService()

# Background thread for rate updates
def start_rate_updater():
    def update_rates():
        while True:
            exchange_rate_service.update_rate()
            time.sleep(3600)  # Update every hour
    thread = threading.Thread(target=update_rates, daemon=True)
    thread.start()
