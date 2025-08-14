import os
import requests
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CryptoPaymentProcessor:
    def __init__(self):
        self.nowpayments_api_key = os.getenv("NOWPAYMENTS_API_KEY", "")
        self.nowpayments_url = "https://api.nowpayments.io/v1"
        self.coinbase_api_key = os.getenv("COINBASE_API_KEY", "")
        self.coinbase_webhook_secret = os.getenv("COINBASE_WEBHOOK_SECRET", "")
        
    def create_nowpayments_invoice(self, amount_usd: float, user_id: str, description: str) -> Dict:
        """Create a crypto payment invoice using NOWPayments"""
        if not self.nowpayments_api_key:
            return {"error": "NOWPayments API key not configured"}
            
        payload = {
            "price_amount": amount_usd,
            "price_currency": "usd",
            "pay_currency": "usdttrc20",
            "ipn_callback_url": f"{os.getenv('WEBHOOK_URL', '')}/webhook/nowpayments",
            "order_id": f"learn4cash_{user_id}_{int(datetime.now().timestamp())}",
            "order_description": description
        }
        
        headers = {
            "x-api-key": self.nowpayments_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.nowpayments_url}/invoice",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NOWPayments error: {e}")
            return {"error": str(e)}
    
    def create_coinbase_charge(self, amount_usd: float, user_id: str, description: str) -> Dict:
        """Create a crypto payment charge using Coinbase Commerce"""
        if not self.coinbase_api_key:
            return {"error": "Coinbase API key not configured"}
            
        payload = {
            "name": "Learn4Cash Tokens",
            "description": description,
            "pricing_type": "fixed_price",
            "local_price": {
                "amount": str(amount_usd),
                "currency": "USD"
            },
            "metadata": {
                "user_id": str(user_id),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        headers = {
            "X-CC-Api-Key": self.coinbase_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://api.commerce.coinbase.com/charges",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Coinbase error: {e}")
            return {"error": str(e)}
    
    def verify_coinbase_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Coinbase webhook signature"""
        if not self.coinbase_webhook_secret:
            return False
            
        try:
            expected_signature = hmac.new(
                self.coinbase_webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return False
    
    def check_payment_status(self, payment_id: str, provider: str) -> Dict:
        """Check payment status from crypto provider"""
        if provider == "nowpayments":
            return self.check_nowpayments_status(payment_id)
        elif provider == "coinbase":
            return self.check_coinbase_status(payment_id)
        return {"error": "Unknown provider"}
    
    def check_nowpayments_status(self, payment_id: str) -> Dict:
        """Check NOWPayments payment status"""
        headers = {"x-api-key": self.nowpayments_api_key}
        try:
            response = requests.get(
                f"{self.nowpayments_url}/payment/{payment_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NOWPayments status check error: {e}")
            return {"error": str(e)}
    
    def check_coinbase_status(self, charge_id: str) -> Dict:
        """Check Coinbase Commerce charge status"""
        headers = {"X-CC-Api-Key": self.coinbase_api_key}
        try:
            response = requests.get(
                f"https://api.commerce.coinbase.com/charges/{charge_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Coinbase status check error: {e}")
            return {"error": str(e)}

# Global instance
crypto_processor = CryptoPaymentProcessor()

def get_crypto_processor():
    return crypto_processor
