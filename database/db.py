from pymongo import MongoClient
from config import Config

def get_db():
    client = MongoClient(Config.MONGO_URI)
    db = client['table_banking_06initiates']
    # Ensure indexes on frequently queried fields for better performance
    db.transactions.create_index("member_id")
    db.loans.create_index("member_id")
    return db

db = get_db()
