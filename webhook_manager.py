#!/usr/bin/env python3
"""
Webhook Manager Utility for LearnEarnAfrica Bot
This utility helps manage and update webhook URLs for the Telegram bot and payment processors.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebhookManager:
    def __init__(self, env_file_path=".env"):
        self.env_file_path = Path(env_file_path)
        self.env_vars = {}
        
    def load_env_file(self):
        """Load environment variables from .env file if it exists"""
        if not self.env_file_path.exists():
            logger.warning(f"Environment file {self.env_file_path} does not exist. Creating new one.")
            return {}
            
        try:
            with open(self.env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.env_vars[key.strip()] = value.strip()
            logger.info(f"Loaded {len(self.env_vars)} environment variables from {self.env_file_path}")
            return self.env_vars
        except Exception as e:
            logger.error(f"Error reading environment file: {e}")
            return {}
    
    def save_env_file(self):
        """Save environment variables to .env file"""
        try:
            with open(self.env_file_path, 'w') as f:
                for key, value in self.env_vars.items():
                    f.write(f"{key}={value}\n")
            logger.info(f"Saved {len(self.env_vars)} environment variables to {self.env_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving environment file: {e}")
            return False
    
    def set_webhook_url(self, webhook_url):
        """Set the WEBHOOK_URL environment variable"""
        if not webhook_url.startswith(('http://', 'https://')):
            logger.warning("Webhook URL should start with http:// or https://")
        
        self.env_vars['WEBHOOK_URL'] = webhook_url
        logger.info(f"Set WEBHOOK_URL to: {webhook_url}")
        return True
    
    def get_webhook_url(self):
        """Get the current WEBHOOK_URL"""
        return self.env_vars.get('WEBHOOK_URL', 'Not set')
    
    def show_current_config(self):
        """Show current webhook configuration"""
        webhook_url = self.get_webhook_url()
        print(f"\n📋 Current Webhook Configuration:")
        print(f"   WEBHOOK_URL: {webhook_url}")
        
        if webhook_url != 'Not set':
            print(f"\n🔗 Webhook Endpoints:")
            print(f"   Telegram Bot: {webhook_url}/webhook")
            print(f"   NOWPayments: {webhook_url}/webhook/nowpayments")
        print()
    
    def test_webhook_url(self):
        """Test if the webhook URL is accessible"""
        webhook_url = self.get_webhook_url()
        if webhook_url == 'Not set':
            logger.error("No webhook URL set. Please set a webhook URL first.")
            return False
        
        try:
            import requests
            response = requests.get(webhook_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Webhook URL {webhook_url} is accessible")
                return True
            else:
                logger.warning(f"⚠️ Webhook URL returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Webhook URL is not accessible: {e}")
            return False
        except ImportError:
            logger.warning("⚠️ requests module not available. Cannot test webhook URL.")
            return False

def main():
    parser = argparse.ArgumentParser(description="Manage webhook configuration for LearnEarnAfrica Bot")
    parser.add_argument('--set', '-s', help='Set webhook URL (e.g., https://example.com)')
    parser.add_argument('--show', action='store_true', help='Show current webhook configuration')
    parser.add_argument('--test', action='store_true', help='Test if webhook URL is accessible')
    parser.add_argument('--env-file', default='.env', help='Path to .env file (default: .env)')
    
    args = parser.parse_args()
    
    # Initialize webhook manager
    manager = WebhookManager(args.env_file)
    manager.load_env_file()
    
    if args.set:
        # Set new webhook URL
        manager.set_webhook_url(args.set)
        if manager.save_env_file():
            print(f"✅ Successfully updated webhook URL to: {args.set}")
            manager.show_current_config()
        else:
            print("❌ Failed to update webhook configuration")
            sys.exit(1)
    
    if args.show:
        manager.show_current_config()
    
    if args.test:
        if manager.test_webhook_url():
            print("✅ Webhook test completed successfully")
        else:
            print("❌ Webhook test failed")
            sys.exit(1)
    
    # If no arguments provided, show current config
    if not any([args.set, args.show, args.test]):
        manager.show_current_config()
        print("💡 Usage: python webhook_manager.py --set <url> | --show | --test")
        print("   --set <url>    Set new webhook URL")
        print("   --show         Show current configuration")
        print("   --test         Test webhook URL accessibility")

if __name__ == "__main__":
    main()
