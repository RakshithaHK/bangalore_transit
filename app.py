"""Flask dashboard. Local: python app.py  | Production: gunicorn app:app"""
import os
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
import pipelines as P

app = Flask(__name__)
db = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))[os.getenv("DB_NAME", "bangalore_transit")]

def flt(use_day=True):
    """Build a $match filter from ?line=Purple|Green and ?day=weekday|weekend."""
    m, line, day = {}, request.args.get("line"), request.args.get("day")
    if line in ("Purple", "Green"):
        m["station_id"] = {"$regex": "^" + line[0]}
    if use_day and day in ("weekday", "weekend"):
        m["is_weekend"] = day == "weekend"
    return m

def agg(coll, pipe, m=None):
    return list(db[coll].aggregate([{"$match": m or {}}] + pipe))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/summary")
def summary():
    trend = agg("ridership", P.DAILY_TREND, flt())
    total = sum(d["total"] for d in trend)
    top = agg("ridership", P.TOP_STATIONS, flt())
    peaks = agg("ridership", P.PEAK_HOURS, flt())
    dt = {d["day_type"]: d["avg_station_day"] for d in agg("ridership", P.WEEKDAY_VS_WEEKEND, flt(False))}
    drop = round((1 - dt["Weekend"] / dt["Weekday"]) * 100, 1) if dt.get("Weekday") and dt.get("Weekend") else None
    return jsonify(total=total, avg_day=round(total / len(trend)) if trend else 0,
                   busiest=top[0] if top else None,
                   peak_hour=max(peaks, key=lambda x: x["total"]) if peaks else None, weekend_drop=drop)

@app.route("/api/top-stations")
def top_stations():
    return jsonify(agg("ridership", P.TOP_STATIONS, flt()))

@app.route("/api/peak-hours")
def peak_hours():
    return jsonify(agg("ridership", P.PEAK_HOURS, flt()))

@app.route("/api/daily-trend")
def daily_trend():
    return jsonify(agg("ridership", P.DAILY_TREND, flt()))

@app.route("/api/bmtc-routes")
def bmtc_routes():
    return jsonify(agg("bmtc_ridership", P.BMTC_TOP_ROUTES))

@app.route("/api/stations")
def stations():
    return jsonify(list(db.stations.find({}, {"_id": 0, "station_id": 1, "name": 1, "line": 1}).sort("name", 1)))

@app.route("/api/station/<sid>")
def station(sid):
    st = db.stations.find_one({"station_id": sid}, {"_id": 0})
    if not st:
        return jsonify(error="unknown station"), 404
    rows = agg("ridership", [{"$unwind": "$hourly"},
        {"$group": {"_id": {"h": "$hourly.hour", "w": "$is_weekend"}, "avg": {"$avg": "$hourly.entries"}}},
        {"$sort": {"_id.h": 1}},
        {"$project": {"_id": 0, "hour": "$_id.h", "weekend": "$_id.w", "avg": {"$round": ["$avg", 0]}}}], {"station_id": sid})
    return jsonify(station=st, rows=rows)

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
