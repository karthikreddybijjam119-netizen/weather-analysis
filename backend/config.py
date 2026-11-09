import os

import mysql.connector

def connect():
    mydb=mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ["DB_PASSWORD"],
        database="weather_analysis"
    )
    return mydb
