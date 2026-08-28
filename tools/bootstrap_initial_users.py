"""One-time production bootstrap; prints generated passwords once."""
import os
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_urlsafe
from bson import ObjectId

for line in Path("apps/api/.env").read_text().splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"')
from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.auth.passwords import hash_password

s = Settings.from_env(); db = MongoClientFactory.create(s); now = datetime.now(UTC)
users = [("yago@wtgseguros.com.br","Yago","admin"),("andre@wtgseguros.com.br","André","admin"),("renato@wtgseguros.com.br","Renato","seller"),("sandracristina@wtgseguros.com.br","Sandra","seller"),("jessicaalmeida@wtgseguros.com.br","Jessica","seller"),("nelmacastro@wtgseguros.com.br","Nelma","seller")]
seller_ids = []
for email, name, role in users:
    existing = db.users.find_one({"emailNormalized": email})
    if existing:
        uid, password = existing["_id"], "(já existente)"
    else:
        uid, password = ObjectId(), token_urlsafe(12)
        db.users.insert_one({"_id":uid,"email":email,"emailNormalized":email,"fullName":name,"role":role,"active":True,"passwordHash":hash_password(password),"createdAt":now,"updatedAt":now})
    print(email, password)
    if role == "seller": seller_ids.append(uid)
for position, uid in enumerate(seller_ids, 1):
    db.seller_queue.update_one({"sellerId":uid},{"$set":{"position":position,"paused":False},"$setOnInsert":{"sellerId":uid}},upsert=True)
    db.skip_balances.update_one({"sellerId":uid},{"$setOnInsert":{"sellerId":uid,"balance":0}},upsert=True)
db.queue_state.update_one({"_id":"global"},{"$setOnInsert":{"nextSellerId":seller_ids[0],"version":0,"updatedAt":now}},upsert=True)
print("BOOTSTRAP_OK")
