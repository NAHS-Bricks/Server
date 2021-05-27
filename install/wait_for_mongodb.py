from pymongo import MongoClient, errors
import sys

mongoClient = MongoClient(host='localhost', port=27017, serverSelectionTimeoutMS=2000)
while(True):
    try:
        mongoClient.server_info()
        print("MongoDB started ... continue")
        sys.exit(0)
    except errors.ServerSelectionTimeoutError:
        print("MongoDB pending ... waiting")
    except Exception:
        print("MongoDB unknown error ... aborting")
        sys.exit(1)
