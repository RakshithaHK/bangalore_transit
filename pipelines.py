"""Aggregation pipelines shared by queries.py and the dashboard."""
_LOOKUP_ST = {"$lookup": {"from": "stations", "localField": "station_id", "foreignField": "station_id", "as": "s"}}

TOP_STATIONS = [
    {"$group": {"_id": "$station_id", "total": {"$sum": "$total_entries"}, "avg_daily": {"$avg": "$total_entries"}}},
    {"$sort": {"total": -1}}, {"$limit": 10},
    {"$lookup": {"from": "stations", "localField": "_id", "foreignField": "station_id", "as": "s"}},
    {"$unwind": "$s"},
    {"$project": {"_id": 0, "station": "$s.name", "line": "$s.line", "total": 1, "avg_daily": {"$round": ["$avg_daily", 0]}}}]

PEAK_HOURS = [
    {"$unwind": "$hourly"},
    {"$group": {"_id": "$hourly.hour", "total": {"$sum": "$hourly.entries"}}},
    {"$sort": {"_id": 1}}, {"$project": {"_id": 0, "hour": "$_id", "total": 1}}]

STATION_PEAK_HOUR = [
    {"$unwind": "$hourly"},
    {"$group": {"_id": {"s": "$station_id", "h": "$hourly.hour"}, "total": {"$sum": "$hourly.entries"}}},
    {"$sort": {"total": -1}},
    {"$group": {"_id": "$_id.s", "peak_hour": {"$first": "$_id.h"}, "peak_total": {"$first": "$total"}}},
    {"$sort": {"peak_total": -1}}, {"$limit": 10},
    {"$lookup": {"from": "stations", "localField": "_id", "foreignField": "station_id", "as": "s"}},
    {"$unwind": "$s"}, {"$project": {"_id": 0, "station": "$s.name", "peak_hour": 1, "peak_total": 1}}]

LINE_SPLIT = [
    _LOOKUP_ST, {"$unwind": "$s"},
    {"$group": {"_id": "$s.line", "total": {"$sum": "$total_entries"}}},
    {"$project": {"_id": 0, "line": "$_id", "total": 1}}]

WEEKDAY_VS_WEEKEND = [
    {"$group": {"_id": "$is_weekend", "avg_station_day": {"$avg": "$total_entries"}}},
    {"$project": {"_id": 0, "day_type": {"$cond": ["$_id", "Weekend", "Weekday"]},
                  "avg_station_day": {"$round": ["$avg_station_day", 0]}}}]

DAILY_TREND = [
    {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "total": {"$sum": "$total_entries"}}},
    {"$sort": {"_id": 1}}, {"$project": {"_id": 0, "date": "$_id", "total": 1}}]

BMTC_TOP_ROUTES = [
    {"$group": {"_id": "$route_no", "passengers": {"$sum": "$passengers"}, "revenue": {"$sum": "$revenue_inr"}}},
    {"$sort": {"passengers": -1}}, {"$limit": 10},
    {"$lookup": {"from": "bmtc_routes", "localField": "_id", "foreignField": "route_no", "as": "r"}},
    {"$unwind": "$r"},
    {"$project": {"_id": 0, "route": "$_id", "path": {"$concat": ["$r.origin", " - ", "$r.destination"]},
                  "type": "$r.type", "passengers": 1, "revenue": 1}}]

BMTC_BY_TYPE = [
    {"$lookup": {"from": "bmtc_routes", "localField": "route_no", "foreignField": "route_no", "as": "r"}},
    {"$unwind": "$r"},
    {"$group": {"_id": "$r.type", "avg_daily_passengers": {"$avg": "$passengers"}, "revenue": {"$sum": "$revenue_inr"}}},
    {"$sort": {"revenue": -1}},
    {"$project": {"_id": 0, "type": "$_id", "avg_daily_passengers": {"$round": ["$avg_daily_passengers", 0]}, "revenue": 1}}]
