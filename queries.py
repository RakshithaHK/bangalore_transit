"""CRUD + sorting/limiting + aggregation demo. Run: python queries.py"""
import os
from pymongo import MongoClient, DESCENDING
import pipelines as P

db = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))[os.getenv("DB_NAME", "bangalore_transit")]

def show(title, docs):
    print(f"\n=== {title} ===")
    for d in docs:
        print(d)

# ---------- CREATE ----------
db.stations.insert_one({"station_id": "T99", "name": "Test Station", "line": "Purple", "sequence": 99, "interchange": False})
print("Collections:", db.list_collection_names())
print("Documents -> ridership:", db.ridership.count_documents({}), "| bmtc_ridership:", db.bmtc_ridership.count_documents({}))

# ---------- READ / FILTER / SORT / LIMIT ----------
show("Interchange stations", db.stations.find({"interchange": True}, {"_id": 0}))
show("Green line stations (first 5)", db.stations.find({"line": "Green"}, {"_id": 0, "name": 1}).sort("sequence", 1).limit(5))
show("Top 5 single-day station records", db.ridership.find({}, {"_id": 0, "station_id": 1, "date": 1, "total_entries": 1})
     .sort("total_entries", DESCENDING).limit(5))
show("Weekend days with >40000 entries", db.ridership.find({"is_weekend": True, "total_entries": {"$gt": 40000}},
     {"_id": 0, "station_id": 1, "day_of_week": 1, "total_entries": 1}).limit(5))
show("AC or Vayu Vajra routes", db.bmtc_routes.find({"type": {"$in": ["AC", "Vayu Vajra"]}}, {"_id": 0, "route_no": 1, "type": 1}))

# ---------- UPDATE ----------
r = db.stations.update_one({"name": "Majestic"}, {"$set": {"facilities": ["Lift", "Escalator", "Parking"]}})
print("\nupdate_one modified:", r.modified_count)
r = db.bmtc_routes.update_many({"type": "AC"}, {"$inc": {"buses": 2}})
print("update_many modified:", r.modified_count)

# ---------- DELETE ----------
print("delete_one deleted:", db.stations.delete_one({"station_id": "T99"}).deleted_count)

# ---------- AGGREGATION ----------
show("Top 10 busiest stations", db.ridership.aggregate(P.TOP_STATIONS))
show("System-wide entries by hour (peak hours)", db.ridership.aggregate(P.PEAK_HOURS))
show("Peak hour of busiest stations", db.ridership.aggregate(P.STATION_PEAK_HOUR))
show("Ridership by line", db.ridership.aggregate(P.LINE_SPLIT))
show("Weekday vs weekend (avg entries per station-day)", db.ridership.aggregate(P.WEEKDAY_VS_WEEKEND))
show("Daily trend (first 7 days)", list(db.ridership.aggregate(P.DAILY_TREND))[:7])
show("BMTC top routes", db.bmtc_ridership.aggregate(P.BMTC_TOP_ROUTES))
show("BMTC by bus type", db.bmtc_ridership.aggregate(P.BMTC_BY_TYPE))
