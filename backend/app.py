from flask import Flask, jsonify, request, send_file
import config
import mysql.connector
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO

app = Flask(__name__)


def fetch_all(query, params=()):
    db = config.connect()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result


def fetch_one(query, params=()):
    db = config.connect()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result


def execute_query(query, params=()):
    db = config.connect()
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    result = cursor.lastrowid
    cursor.close()
    db.close()
    return result


@app.route("/")
def home():
    return jsonify({
        "message": "Weather Data Analysis System API",
        "database": "weather_analysis",
        "tables": [
            "locations",
            "weather_records",
            "weather_summary"
        ],
        "endpoints": [
            "/locations",
            "/weather-records",
            "/weather-summary",
            "/reports/monthly",
            "/reports/location-summary",
            "/reports/high-temperature",
            "/analytics/temperature",
            "/analytics/rainfall",
            "/analytics/weather-numpy",
            "/charts/temperature",
            "/charts/rainfall",
            "/charts/monthly-summary"
        ]
    })


@app.route("/locations", methods=["GET"])
def get_locations():
    return jsonify(fetch_all("SELECT * FROM locations"))


@app.route("/locations", methods=["POST"])
def add_location():
    data = request.get_json()

    required = ["location_name", "state"]

    if not data or any(key not in data for key in required):
        return jsonify({"error": "Provide location_name and state"}), 400

    try:
        location_id = execute_query(
            """INSERT INTO locations
            (location_name, state)
            VALUES (%s, %s)""",
            (data["location_name"], data["state"])
        )

        return jsonify({
            "message": "Location added successfully",
            "location_id": location_id
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/locations/<int:location_id>", methods=["GET"])
def get_location(location_id):
    location = fetch_one(
        "SELECT * FROM locations WHERE location_id = %s",
        (location_id,)
    )

    if not location:
        return jsonify({"error": "Location not found"}), 404

    return jsonify(location)


@app.route("/locations/<int:location_id>", methods=["PUT"])
def update_location(location_id):
    data = request.get_json()

    allowed = ["location_name", "state"]
    updates = [(key, data[key]) for key in allowed if data and key in data]

    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400

    location = fetch_one(
        "SELECT * FROM locations WHERE location_id = %s",
        (location_id,)
    )

    if not location:
        return jsonify({"error": "Location not found"}), 404

    set_clause = ", ".join(f"{key} = %s" for key, value in updates)
    values = [value for key, value in updates]
    values.append(location_id)

    try:
        execute_query(
            f"UPDATE locations SET {set_clause} WHERE location_id = %s",
            tuple(values)
        )

        return jsonify({"message": "Location updated successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/locations/<int:location_id>", methods=["DELETE"])
def delete_location(location_id):
    location = fetch_one(
        "SELECT * FROM locations WHERE location_id = %s",
        (location_id,)
    )

    if not location:
        return jsonify({"error": "Location not found"}), 404

    try:
        execute_query(
            "DELETE FROM locations WHERE location_id = %s",
            (location_id,)
        )

        return jsonify({"message": "Location deleted successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/weather-records", methods=["GET"])
def get_weather_records():
    return jsonify(fetch_all("SELECT * FROM weather_records"))


@app.route("/weather-records", methods=["POST"])
def add_weather_record():
    data = request.get_json()

    required = [
        "observation_date",
        "location",
        "temperature",
        "humidity",
        "rainfall"
    ]

    if not data or any(key not in data for key in required):
        return jsonify({
            "error": "Provide observation_date, location, temperature, humidity and rainfall"
        }), 400

    try:
        record_id = execute_query(
            """INSERT INTO weather_records
            (observation_date, location, temperature, humidity, rainfall)
            VALUES (%s, %s, %s, %s, %s)""",
            (
                data["observation_date"],
                data["location"],
                data["temperature"],
                data["humidity"],
                data["rainfall"]
            )
        )

        return jsonify({
            "message": "Weather record added successfully",
            "record_id": record_id
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/weather-records/<int:record_id>", methods=["GET"])
def get_weather_record(record_id):
    record = fetch_one(
        "SELECT * FROM weather_records WHERE record_id = %s",
        (record_id,)
    )

    if not record:
        return jsonify({"error": "Weather record not found"}), 404

    return jsonify(record)


@app.route("/weather-records/<int:record_id>", methods=["PUT"])
def update_weather_record(record_id):
    data = request.get_json()

    allowed = [
        "observation_date",
        "location",
        "temperature",
        "humidity",
        "rainfall"
    ]

    updates = [(key, data[key]) for key in allowed if data and key in data]

    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400

    record = fetch_one(
        "SELECT * FROM weather_records WHERE record_id = %s",
        (record_id,)
    )

    if not record:
        return jsonify({"error": "Weather record not found"}), 404

    set_clause = ", ".join(f"{key} = %s" for key, value in updates)
    values = [value for key, value in updates]
    values.append(record_id)

    try:
        execute_query(
            f"UPDATE weather_records SET {set_clause} WHERE record_id = %s",
            tuple(values)
        )

        return jsonify({"message": "Weather record updated successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/weather-records/<int:record_id>", methods=["DELETE"])
def delete_weather_record(record_id):
    record = fetch_one(
        "SELECT * FROM weather_records WHERE record_id = %s",
        (record_id,)
    )

    if not record:
        return jsonify({"error": "Weather record not found"}), 404

    try:
        execute_query(
            "DELETE FROM weather_records WHERE record_id = %s",
            (record_id,)
        )

        return jsonify({"message": "Weather record deleted successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/weather-summary", methods=["GET"])
def get_weather_summary():
    query = """
        SELECT
            s.*,
            l.location_name,
            l.state
        FROM weather_summary s
        JOIN locations l ON s.location_id = l.location_id
        ORDER BY s.summary_id
    """

    return jsonify(fetch_all(query))


@app.route("/weather-summary", methods=["POST"])
def add_weather_summary():
    data = request.get_json()

    required = [
        "location_id",
        "month",
        "avg_temperature",
        "max_temperature",
        "min_temperature",
        "total_rainfall",
        "avg_humidity"
    ]

    if not data or any(key not in data for key in required):
        return jsonify({"error": "Provide all weather summary fields"}), 400

    try:
        summary_id = execute_query(
            """INSERT INTO weather_summary
            (location_id, month, avg_temperature, max_temperature,
             min_temperature, total_rainfall, avg_humidity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                data["location_id"],
                data["month"],
                data["avg_temperature"],
                data["max_temperature"],
                data["min_temperature"],
                data["total_rainfall"],
                data["avg_humidity"]
            )
        )

        return jsonify({
            "message": "Weather summary added successfully",
            "summary_id": summary_id
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/weather-summary/<int:summary_id>", methods=["GET"])
def get_weather_summary_by_id(summary_id):
    summary = fetch_one(
        "SELECT * FROM weather_summary WHERE summary_id = %s",
        (summary_id,)
    )

    if not summary:
        return jsonify({"error": "Summary not found"}), 404

    return jsonify(summary)


@app.route("/weather-summary/<int:summary_id>", methods=["PUT"])
def update_weather_summary(summary_id):
    data = request.get_json()

    allowed = [
        "location_id",
        "month",
        "avg_temperature",
        "max_temperature",
        "min_temperature",
        "total_rainfall",
        "avg_humidity"
    ]

    updates = [(key, data[key]) for key in allowed if data and key in data]

    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400

    summary = fetch_one(
        "SELECT * FROM weather_summary WHERE summary_id = %s",
        (summary_id,)
    )

    if not summary:
        return jsonify({"error": "Summary not found"}), 404

    set_clause = ", ".join(f"{key} = %s" for key, value in updates)
    values = [value for key, value in updates]
    values.append(summary_id)

    try:
        execute_query(
            f"UPDATE weather_summary SET {set_clause} WHERE summary_id = %s",
            tuple(values)
        )

        return jsonify({"message": "Weather summary updated successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/weather-summary/<int:summary_id>", methods=["DELETE"])
def delete_weather_summary(summary_id):
    summary = fetch_one(
        "SELECT * FROM weather_summary WHERE summary_id = %s",
        (summary_id,)
    )

    if not summary:
        return jsonify({"error": "Summary not found"}), 404

    try:
        execute_query(
            "DELETE FROM weather_summary WHERE summary_id = %s",
            (summary_id,)
        )

        return jsonify({"message": "Weather summary deleted successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/reports/monthly", methods=["GET"])
def monthly_report():
    query = """
        SELECT
            MONTH(observation_date) AS month_number,
            MONTHNAME(observation_date) AS month_name,
            AVG(temperature) AS avg_temperature,
            MAX(temperature) AS max_temperature,
            MIN(temperature) AS min_temperature,
            SUM(rainfall) AS total_rainfall,
            AVG(humidity) AS avg_humidity
        FROM weather_records
        GROUP BY MONTH(observation_date), MONTHNAME(observation_date)
        ORDER BY month_number
    """

    return jsonify(fetch_all(query))


@app.route("/reports/location-summary", methods=["GET"])
def location_summary():
    query = """
        SELECT
            location,
            COUNT(*) AS total_records,
            AVG(temperature) AS avg_temperature,
            MAX(temperature) AS max_temperature,
            MIN(temperature) AS min_temperature,
            SUM(rainfall) AS total_rainfall,
            AVG(humidity) AS avg_humidity
        FROM weather_records
        GROUP BY location
        ORDER BY location
    """

    return jsonify(fetch_all(query))


@app.route("/reports/high-temperature", methods=["GET"])
def high_temperature():
    threshold = request.args.get("threshold", default=35, type=float)

    query = """
        SELECT *
        FROM weather_records
        WHERE temperature >= %s
        ORDER BY temperature DESC
    """

    return jsonify(fetch_all(query, (threshold,)))


@app.route("/analytics/temperature", methods=["GET"])
def temperature_analysis():
    rows = fetch_all("""
        SELECT
            location,
            AVG(temperature) AS average_temperature
        FROM weather_records
        GROUP BY location
        ORDER BY average_temperature DESC
    """)

    if not rows:
        return jsonify([])

    df = pd.DataFrame(rows)
    df = df.fillna(0)

    return jsonify(df.to_dict(orient="records"))


@app.route("/analytics/rainfall", methods=["GET"])
def rainfall_analysis():
    query = """
        SELECT
            location,
            SUM(rainfall) AS total_rainfall,
            AVG(rainfall) AS average_rainfall
        FROM weather_records
        GROUP BY location
        ORDER BY total_rainfall DESC
    """

    return jsonify(fetch_all(query))


@app.route("/analytics/weather-numpy", methods=["GET"])
def weather_numpy():
    rows = fetch_all("""
        SELECT temperature, humidity, rainfall
        FROM weather_records
    """)

    if not rows:
        return jsonify({
            "average_temperature": 0,
            "maximum_temperature": 0,
            "minimum_temperature": 0,
            "average_humidity": 0,
            "total_rainfall": 0
        })

    temperatures = np.array(
        [float(row["temperature"]) for row in rows]
    )

    humidity = np.array(
        [float(row["humidity"]) for row in rows]
    )

    rainfall = np.array(
        [float(row["rainfall"]) for row in rows]
    )

    return jsonify({
        "average_temperature": float(np.mean(temperatures)),
        "maximum_temperature": float(np.max(temperatures)),
        "minimum_temperature": float(np.min(temperatures)),
        "average_humidity": float(np.mean(humidity)),
        "total_rainfall": float(np.sum(rainfall))
    })


@app.route("/charts/temperature", methods=["GET"])
def temperature_chart():
    rows = fetch_all("""
        SELECT
            location,
            AVG(temperature) AS avg_temperature
        FROM weather_records
        GROUP BY location
        ORDER BY location
    """)

    if not rows:
        return jsonify({"error": "No weather data available"}), 404

    names = [row["location"] for row in rows]
    temperatures = [float(row["avg_temperature"]) for row in rows]

    plt.figure(figsize=(12, 6))
    plt.bar(names, temperatures)
    plt.xlabel("Location")
    plt.ylabel("Average Temperature (°C)")
    plt.title("Average Temperature by Location")
    plt.xticks(rotation=45)
    plt.tight_layout()

    image_data = BytesIO()
    plt.savefig(image_data, format="png")
    image_data.seek(0)
    plt.close()

    return send_file(image_data, mimetype="image/png")


@app.route("/charts/rainfall", methods=["GET"])
def rainfall_chart():
    rows = fetch_all("""
        SELECT
            location,
            SUM(rainfall) AS total_rainfall
        FROM weather_records
        GROUP BY location
        ORDER BY location
    """)

    if not rows:
        return jsonify({"error": "No rainfall data available"}), 404

    names = [row["location"] for row in rows]
    rainfall = [float(row["total_rainfall"]) for row in rows]

    plt.figure(figsize=(12, 6))
    plt.bar(names, rainfall)
    plt.xlabel("Location")
    plt.ylabel("Total Rainfall")
    plt.title("Total Rainfall by Location")
    plt.xticks(rotation=45)
    plt.tight_layout()

    image_data = BytesIO()
    plt.savefig(image_data, format="png")
    image_data.seek(0)
    plt.close()

    return send_file(image_data, mimetype="image/png")


@app.route("/charts/monthly-summary", methods=["GET"])
def monthly_summary_chart():
    rows = fetch_all("""
        SELECT
            l.location_name,
            s.month,
            s.avg_temperature
        FROM weather_summary s
        JOIN locations l ON s.location_id = l.location_id
        ORDER BY s.month, l.location_name
    """)

    if not rows:
        return jsonify({"error": "No summary data available"}), 404

    df = pd.DataFrame(rows)

    pivot = df.pivot(
        index="month",
        columns="location_name",
        values="avg_temperature"
    )

    plt.figure(figsize=(12, 6))

    for location in pivot.columns:
        plt.plot(
            pivot.index,
            pivot[location],
            marker="o",
            label=location
        )

    plt.xlabel("Month")
    plt.ylabel("Average Temperature (°C)")
    plt.title("Monthly Average Temperature by Location")
    plt.xticks([1, 2, 3, 4])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    image_data = BytesIO()
    plt.savefig(image_data, format="png")
    image_data.seek(0)
    plt.close()

    return send_file(image_data, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)