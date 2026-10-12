# Bangalore Metro / BMTC Ridership Analysis (MongoDB)

## Run locally
1. Install Python 3.10+ and MongoDB Community Server (https://www.mongodb.com/try/download/community). Start it (`mongod` or the Windows service).
2. `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. `python generate_data.py`   -> loads ~1,890 daily station docs + 600 BMTC docs
5. `python queries.py`         -> CRUD + aggregation output (take screenshots)
6. `python app.py`             -> open http://localhost:5000

## Deploy (free): MongoDB Atlas + Render
1. Atlas: create free M0 cluster, a DB user, and under Network Access allow 0.0.0.0/0.
   Copy the connection string: `mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/`
2. Load data into Atlas from your PC:
   - Linux/Mac: `export MONGO_URI="<atlas-uri>"`  | Windows: `set MONGO_URI=<atlas-uri>`
   - `python generate_data.py`
3. Push this folder to a GitHub repo.
4. Render.com -> New Web Service -> select repo.
   Build command: `pip install -r requirements.txt`
   Start command: `gunicorn app:app`
   Environment variable: `MONGO_URI` = your Atlas URI
5. Open the Render URL.

## mongosh equivalents (for the report)
use bangalore_transit
db.stations.find({interchange:true})
db.ridership.find().sort({total_entries:-1}).limit(5)
db.ridership.aggregate([{$unwind:"$hourly"},{$group:{_id:"$hourly.hour",total:{$sum:"$hourly.entries"}}},{$sort:{total:-1}},{$limit:3}])
db.ridership.aggregate([{$group:{_id:"$station_id",total:{$sum:"$total_entries"}}},{$sort:{total:-1}},{$limit:10}])
