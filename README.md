# 🚚 Truck Stop & Fuel Optimizer

A Django-based API that calculates the most cost-effective fuel stops for truck routes across the United States.

The application uses **OpenRouteService** for route generation, **Haversine distance calculations** for geographic proximity checks, and locally stored fuel price data to recommend optimal fueling locations while minimizing total fuel cost.

---

## 📋 Problem Statement

Given:

* Start Location (USA)
* Destination Location (USA)
* Vehicle Range = **500 miles**
* Fuel Efficiency = **10 MPG**

The system should:

1. Generate the driving route.
2. Identify required fuel stops.
3. Find fuel stations located near the route.
4. Select the most cost-effective fuel stations.
5. Return:

   * Route geometry
   * Recommended fuel stops
   * Total fuel cost estimate

---

## ✨ Features

* Route generation using OpenRouteService
* Fuel station optimization based on fuel prices
* Multiple fuel stop support for long-distance routes
* Haversine-based geographic distance calculations
* Route response caching
* Fuel station cache warming
* Pre-computed geolocation storage
* Minimal external API usage
* Fast route optimization using local data

---

## 🛠 Tech Stack

### Backend

* Python 3.13+
* Django 6.x
* Django REST Framework

### Database

* MySQL

### Routing Provider

* OpenRouteService

### Caching

* Django Cache Framework

### Geospatial Calculations

* Haversine Formula

---

## 📂 Project Structure

```text
TruckStopAndFuelOptimizer/

├── api/
├── fuel/
├── routing/
├── data/
├── static/
├── templates/
├── tracking_optimizer/
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🗄 Data Model

### FuelStation

Stores truck stop information.

| Field          | Description       |
| -------------- | ----------------- |
| truckstop_name | Truck stop name   |
| address        | Station address   |
| city           | City              |
| state          | State             |
| latitude       | Latitude          |
| longitude      | Longitude         |
| created_at     | Created timestamp |
| updated_at     | Updated timestamp |

### FuelPrice

Stores diesel fuel pricing information.

| Field        | Description       |
| ------------ | ----------------- |
| fuel_station | Related station   |
| retail_price | Fuel price        |
| created_at   | Created timestamp |
| updated_at   | Updated timestamp |

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/chanchalkmaurya/TruckStopAndFuelOptimizer.git

cd TruckStopAndFuelOptimizer
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

### Linux / Mac

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙ Environment Variables

Create a `.env` file inside the project root.

```env
SECRET_KEY=your-secret-key

DEBUG=True

ORS_API_KEY=your-openrouteservice-api-key
```

---

## 🛢 Database Configuration

Update the DATABASES section in `settings.py`.

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "your_database_name",
        "USER": "your_username",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

Run migrations:

```bash
python manage.py makemigrations

python manage.py migrate
```

---

# 📥 Import Fuel Dataset

Import the provided fuel pricing dataset.

```bash
python manage.py import_fuel_data
```

This command:

* Reads the CSV dataset
* Cleans and validates records
* Creates or updates FuelStation records
* Creates or updates FuelPrice records
* Automatically generates station geolocations when required

---

# 🌍 Generate Geolocation Data

If geolocations were not generated during import:

```bash
python manage.py generate_geolocations_data
```

Purpose:

* Convert addresses into coordinates
* Store latitude and longitude permanently
* Prevent future geocoding requests

This command typically runs only once.

---

# ⚡ Warm Station Cache

```bash
python manage.py warm_station_cache
```

Purpose:

* Precompute station lookup information
* Speed up route optimization
* Reduce database lookups during requests

Recommended after every fuel-price refresh.

---

# ▶ Running the Server

```bash
python manage.py runserver
```

Server:

```text
http://localhost:8000
```

---

# 🔌 API Endpoint

## Optimize Route

```http
POST /api/route/
```

### Request

```json
{
  "start": "Dallas, TX",
  "end": "Chicago, IL"
}
```

### Response

```json
{
  "distance_miles": 968,
  "fuel_cost": 412.60,
  "route_geometry" :[
        [
            41.878993,
            -87.660631
        ],
        [
            41.878971,
            -87.66192
        ],
        [
            41.878702,
            -87.661912
        ],
        [.........]
  ],
  "fuel_stops": [
    {
            "station_name": "K AND H TRUCK PLAZA",
            "city": "Gilman",
            "state": "IL",
            "latitude": 40.768396,
            "longitude": -87.990055,
            "price": 3.099,
            "distance_into_route_miles": 86.7,
            "gallons_purchased": 50.0,
            "cost": 154.95
      },
      {.........},
  ]
}
```

---

# ⛽ Fuel Optimization Strategy

## Step 1: Generate Route

The API receives a start and destination location. 2 Search API is required to get the geolocations of source and destinations.
1. start_geoloacation -> OpenRouteService /geocode/search
2. end_geoloacation -> OpenRouteService /geocode/search

OpenRouteService generates:
* Route geometry
* Total distance
* Route coordinates
using start_geolocation, end_geolocation.
Only a single routing API request is typically required.

Note: 3 OpenRouteService API call can be reduced to 1 if we pass the geolocation from frontend somehow.

---

## Step 2: Find Stations Near the Route

All fuel stations are stored locally with latitude and longitude coordinates.

The application uses the **Haversine Formula** to calculate distances between:

* Route coordinates
* Fuel station coordinates

Stations within a configurable distance from the route are considered potential fuel stops.

This avoids expensive external API calls and keeps the optimization process fast.

---

## Step 3: Determine Reachable Stations

Vehicle assumptions:

* Maximum Range = 500 Miles
* Fuel Efficiency = 10 MPG

Only stations reachable within the remaining driving range are considered.

Stations outside the reachable distance are ignored.

---

## Step 4: Select Cheapest Reachable Station

Among all candidate stations:

* Compare fuel prices
* Select the most cost-effective station
* Minimize total trip fuel expenses

The optimizer focuses on overall fuel savings rather than simply selecting the closest station.

---

## Step 5: Repeat Until Destination

After selecting a fuel stop:

1. The selected station becomes the new starting point.
2. Remaining route distance is calculated.
3. Reachable stations are identified again.
4. The next optimal stop is selected.

The process continues until the destination can be reached without additional refueling.

---

# 🌎 Why Haversine Formula?

Latitude and longitude coordinates represent locations on a spherical Earth.

The Haversine Formula calculates the great-circle distance between two geographic points.

It is used to:

* Measure proximity between route points and fuel stations
* Identify stations near the route
* Determine station reachability
* Support fast geographic filtering without external services

This significantly reduces API usage and improves response times.

---

# 💰 Fuel Cost Calculation

Vehicle Assumptions:

* Maximum Range = 500 Miles
* Fuel Efficiency = 10 MPG

### Fuel Consumption

```text
Gallons Required = Total Distance / 10
```

### Fuel Cost

```text
Total Fuel Cost = Σ (Gallons Purchased × Fuel Price)
```

---

# ⚡ Performance Optimizations

## Route Caching

Routes are cached using:

```text
Origin + Destination
```

This avoids repeated OpenRouteService requests.

---

## Geolocation Persistence

Fuel station coordinates are permanently stored in the database.

No runtime geocoding is required.

---

## Station Cache

Nearby station lookups are precomputed using:

```bash
python manage.py warm_station_cache
```

This minimizes expensive database scans.

---

## External API Usage

Typical request:

* 1 OpenRouteService Route API Call

Ideal request:

* No geocoding requests
* All optimization performed locally

---

# 🔄 Daily Data Refresh Process

When a new fuel-price dataset is received:

```bash
python manage.py import_fuel_data

python manage.py warm_station_cache
```

Geolocation regeneration is not required unless new stations are introduced.

---

# 🏗 One-Time Deployment Setup

Run once after initial deployment:

```bash
python manage.py import_fuel_data

python manage.py generate_geolocations_data

python manage.py warm_station_cache
```

---

# ⚠ Special Cases

### Long Distance Routes

Automatically supports multiple fuel stops.

### No Nearby Station Found

Falls back to the nearest valid station within an acceptable distance.

### Duplicate Fuel Records

Import process performs updates rather than creating duplicate records.

### OpenRouteService Rate Limits

Route caching reduces external API consumption.

### Daily Dataset Updates

Fuel prices can be refreshed without recalculating station coordinates.

---

# 🔮 Future Improvements

* Redis Cache
* Celery Background Tasks
* PostgreSQL + PostGIS
* Route History Storage
* Fuel Price Trend Analysis
* Multi-Vehicle Support
* EV Charging Optimization
* Advanced Cost Prediction

---

# 🎥 Loom Demo

The Loom demonstration should cover:

1. Project overview
2. Database population
3. Dataset import
4. Route optimization request in Postman
5. Route response
6. Fuel stop recommendations
7. Fuel cost calculation
8. Brief code walkthrough

**Target Duration:** 5 Minutes Maximum

Video Link: 
