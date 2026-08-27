"""F\u00e1brica de clientes MongoDB restrita ao backend."""

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase

from gerec_api.config import Settings


class MongoClientFactory:
    """Cria o handle de banco sem expor a URI fora do processo servidor."""

    @staticmethod
    def create(settings: Settings) -> MongoDatabase:
        client = MongoClient(settings.mongodb_uri)
        return client[settings.mongodb_database]
