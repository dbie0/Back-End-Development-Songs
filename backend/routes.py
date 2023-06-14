from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=['GET'])
def health_check():
    return {'status': 'ok'}

@app.route("/count")
def count():
    return {'count': db.songs.count_documents({})}

@app.route("/song", methods=["GET"])
def songs():
    return {'songs': json_util.dumps(list(db.songs.find({})))}

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    return {'songs': json_util.dumps(list(db.songs.find({'id': id})))}

@app.route("/song", methods=["POST"])
def create_song():
    body = request.get_json()
    if db.songs.find_one({'id': body.get('id')}):
        return {"Message": f"song with id {body.get('id')} already present"}, 302
    iid = str(db.songs.insert_one(body).inserted_id)
    return {"inserted id":{"$oid": iid}}

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    body = request.get_json()
    if (song := db.songs.find_one({'id': id})):
        db.songs.update_one({'id': id}, {'$set': body})
        body.update({'id': id, "_id": str(song["_id"])})
        return body
    return {"message":"song found, but nothing updated"}, 404

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):

    r = db.songs.delete_one({"id": id})
    if r.deleted_count:
        return "", 204
    return {"message":"song not found"}, 404