"""Generates synthetic Namma Metro + BMTC ridership data and loads it into MongoDB."""
import os, math, random
from datetime import datetime, timedelta
from pymongo import MongoClient

db = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))[os.getenv("DB_NAME", "bangalore_transit")]
random.seed(42)

PURPLE = ["Whitefield (Kadugodi)", "Hopefarm Channasandra", "Kadugodi Tree Park", "Pattandur Agrahara",
          "Sri Sathya Sai Hospital", "Nallurhalli", "Kundalahalli", "Seetharamapalya", "Hoodi",
          "Garudacharapalya", "Singayyanapalya", "KR Puram", "Benniganahalli", "Baiyappanahalli",
          "Swami Vivekananda Road", "Indiranagar", "Halasuru", "Trinity", "MG Road", "Cubbon Park",
          "Vidhana Soudha", "Sir M Visvesvaraya", "Majestic", "City Railway Station", "Magadi Road",
          "Hosahalli", "Vijayanagar", "Attiguppe", "Deepanjali Nagar", "Mysuru Road", "Nayandahalli",
          "Rajarajeshwari Nagar", "Jnanabharathi", "Pattanagere", "Kengeri Bus Terminal", "Kengeri"]
GREEN = ["Nagasandra", "Dasarahalli", "Jalahalli", "Peenya Industry", "Peenya", "Yeshwanthpur",
         "Sandal Soap Factory", "Mahalakshmi", "Rajajinagar", "Kuvempu Road", "Srirampura", "Sampige Road",
         "Chickpete", "KR Market", "National College", "Lalbagh", "South End Circle", "Jayanagar", "RV Road",
         "Banashankari", "JP Nagar", "Yelachenahalli", "Konanakunte Cross", "Doddakallasandra",
         "Vajarahalli", "Thalaghattapura", "Silk Institute"]
BOOST = {"Majestic": 3.5, "MG Road": 3, "Indiranagar": 2.2, "KR Puram": 2.2, "Baiyappanahalli": 2,
         "Whitefield (Kadugodi)": 2, "Yeshwanthpur": 2, "Jayanagar": 1.8, "KR Market": 1.8,
         "Banashankari": 1.6, "Vidhana Soudha": 1.6, "Cubbon Park": 1.5, "Trinity": 1.5, "Kengeri": 1.4,
         "Nagasandra": 1.4, "Rajajinagar": 1.4, "Halasuru": 1.3, "Hoodi": 1.3}
INTERCHANGE = {"Majestic", "RV Road"}
HOURS = list(range(6, 23))
DAYS = 30
START = datetime(2026, 9, 1)

stations, base = [], {}
for line, names, pre in (("Purple", PURPLE, "P"), ("Green", GREEN, "G")):
    for i, n in enumerate(names, 1):
        sid = f"{pre}{i:02d}"
        stations.append({"station_id": sid, "name": n, "line": line, "sequence": i,
                         "interchange": n in INTERCHANGE})
        base[sid] = random.randint(4000, 8000) * BOOST.get(n, 1)

def weights(weekend):
    w = [(math.exp(-((h - 13) ** 2) / 30) + 0.3) if weekend else
         (math.exp(-((h - 9) ** 2) / 3) + 1.1 * math.exp(-((h - 18) ** 2) / 4) + 0.2) for h in HOURS]
    s = sum(w)
    return [x / s for x in w]

WK, WE = weights(False), weights(True)
ridership = []
for s in stations:
    for d in range(DAYS):
        day = START + timedelta(days=d)
        weekend = day.weekday() >= 5
        total = base[s["station_id"]] * (0.7 if weekend else 1) * random.uniform(0.9, 1.1)
        hourly = [{"hour": h, "entries": int(total * p * random.uniform(0.92, 1.08))}
                  for h, p in zip(HOURS, WE if weekend else WK)]
        ridership.append({"station_id": s["station_id"], "date": day, "day_of_week": day.strftime("%A"),
                          "is_weekend": weekend, "hourly": hourly,
                          "total_entries": sum(x["entries"] for x in hourly)})

# NOTE: route numbers/origins are illustrative; passenger counts are synthetic.
ROUTES = [("500D", "Hebbal", "Silk Board", "AC", 40, 24), ("335E", "Kadugodi", "Majestic", "Ordinary", 55, 25),
          ("500K", "Kempegowda Airport", "Kengeri", "AC", 30, 52), ("G4", "Majestic", "Electronic City", "AC", 35, 22),
          ("356CW", "Majestic", "Whitefield", "Ordinary", 45, 21), ("201", "Majestic", "Banashankari", "Ordinary", 50, 14),
          ("210", "Majestic", "Kengeri", "Ordinary", 48, 18), ("KIA-5", "Majestic", "Kempegowda Airport", "Vayu Vajra", 25, 35),
          ("KIA-8", "Indiranagar", "Kempegowda Airport", "Vayu Vajra", 20, 40), ("276", "Majestic", "Yelahanka", "Ordinary", 38, 22),
          ("V-500A", "Banashankari", "Whitefield", "AC", 28, 36), ("MF-1", "KR Puram", "Majestic", "Ordinary", 42, 16),
          ("144", "Majestic", "Jayanagar", "Ordinary", 36, 10), ("G2", "Majestic", "Sarjapur", "AC", 26, 25),
          ("298", "Yeshwanthpur", "KR Market", "Ordinary", 30, 14), ("401", "Majestic", "Hosur Road", "Ordinary", 33, 20),
          ("600", "Hebbal", "Banashankari", "Ordinary", 29, 24), ("365", "Shivajinagar", "Marathahalli", "Ordinary", 31, 15),
          ("G10", "Jayanagar", "Whitefield", "AC", 22, 30), ("AS-4", "KR Puram", "Kempegowda Airport", "AC", 18, 38)]
routes = [dict(zip(("route_no", "origin", "destination", "type", "buses", "distance_km"), r)) for r in ROUTES]
bmtc = []
for r in routes:
    mean = r["buses"] * random.randint(450, 700)
    for d in range(DAYS):
        day = START + timedelta(days=d)
        p = int(mean * (0.75 if day.weekday() >= 5 else 1) * random.uniform(0.9, 1.1))
        bmtc.append({"route_no": r["route_no"], "date": day, "passengers": p,
                     "revenue_inr": int(p * random.uniform(18, 35))})

for c in ("stations", "ridership", "bmtc_routes", "bmtc_ridership"):
    db[c].drop()
db.stations.insert_many(stations); db.ridership.insert_many(ridership)
db.bmtc_routes.insert_many(routes); db.bmtc_ridership.insert_many(bmtc)
db.stations.create_index("station_id", unique=True)
db.ridership.create_index([("station_id", 1), ("date", 1)])
db.bmtc_ridership.create_index([("route_no", 1), ("date", 1)])
print(f"stations={len(stations)} ridership={len(ridership)} bmtc_routes={len(routes)} bmtc_ridership={len(bmtc)}")
