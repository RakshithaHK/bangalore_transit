# Bangalore Metro / BMTC Ridership Analysis (MongoDB)

## Run locally
1. Install Python 3.10+ and MongoDB Community Server (https://www.mongodb.com/try/download/community). Start it (`mongod` or the Windows service).
2. `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. `python generate_data.py`   -> loads ~1,890 daily station docs + 600 BMTC docs into the local MongoDB
5. `python queries.py`         -> CRUD + aggregation output (take screenshots)
6. `python app.py`             -> open http://localhost:5000

## Deploy (free): MongoDB Atlas + Render
1. Atlas: create free M0 cluster, a DB user, and under Network Access allow 0.0.0.0/0.
   Copy the connection string: `mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/`
2. Load data into Atlas from your PC. Set `MONGO_URI` to the Atlas connection string and use the same `DB_NAME` that the web service will use:
   - PowerShell: `$env:MONGO_URI = "mongodb+srv://<user>:<password>@<cluster-host>/?retryWrites=true&w=majority"`
   - Command Prompt: `set "MONGO_URI=mongodb+srv://<user>:<password>@<cluster-host>/?retryWrites=true&w=majority"`
   - Linux/macOS: `export MONGO_URI="mongodb+srv://<user>:<password>@<cluster-host>/?retryWrites=true&w=majority"`
   - In that same terminal, run `python generate_data.py` once. This script replaces the demo collections each time it runs; do not run it again if you need to preserve changes in those collections.
3. Push this folder to a GitHub repo.
4. Render.com -> New Web Service -> select repo.
   Build command: `pip install -r requirements.txt`
   Start command: `gunicorn app:app`
   Environment variables: `MONGO_URI` = the same Atlas URI used to load the data; `DB_NAME` = the same database name (defaults to `bangalore_transit`)
5. Open the Render URL.

The app intentionally uses `mongodb://localhost:27017` as its default only for local development. On Render or Vercel, it refuses to start if `MONGO_URI` is missing rather than silently connecting to an unavailable local MongoDB. For Vercel, add `MONGO_URI` and (if changed from the default) `DB_NAME` under **Project Settings -> Environment Variables**, enable them for the deployment environment, and redeploy. If the site opens but shows no data, check that the Atlas cluster allows connections from the hosting service, and that the seed command and hosted app use the same `MONGO_URI` and `DB_NAME`.

## mongosh equivalents (for the report)
use bangalore_transit
db.stations.find({interchange:true})
db.ridership.find().sort({total_entries:-1}).limit(5)
db.ridership.aggregate([{$unwind:"$hourly"},{$group:{_id:"$hourly.hour",total:{$sum:"$hourly.entries"}}},{$sort:{total:-1}},{$limit:3}])
db.ridership.aggregate([{$group:{_id:"$station_id",total:{$sum:"$total_entries"}}},{$sort:{total:-1}},{$limit:10}])
