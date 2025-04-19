import logging
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

class BaseTools:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.es_client = self._create_elasticsearch_client()

    def _get_es_config(self):
        """Get Elasticsearch configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        config = {
            "host": os.getenv("ELASTIC_HOST"),
            "username": os.getenv("ELASTIC_USERNAME"),
            "password": os.getenv("ELASTIC_PASSWORD")
        }
        
        return config

    def _create_elasticsearch_client(self) -> Elasticsearch:
        """Create and return an Elasticsearch client using configuration from environment."""
        config = self._get_es_config()
        
        # ถ้ามีทั้ง username และ password ให้ใช้ basic_auth
        if config["username"] and config["password"]:
            return Elasticsearch(
                config["host"],
                basic_auth=(config["username"], config["password"]),
                verify_certs=False
            )
        
        # ถ้าไม่มี credentials ให้เชื่อมต่อโดยไม่ใช้ authentication
        return Elasticsearch(
            config["host"],
            verify_certs=False
        )