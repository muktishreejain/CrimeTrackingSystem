import os
import mysql.connector
from mysql.connector import pooling


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "admin"),
    "database": os.getenv("DB_NAME", "CrimeTrackingSystem"),
}


pool = pooling.MySQLConnectionPool(
    pool_name="crime_tracking_pool",
    pool_size=int(os.getenv("DB_POOL_SIZE", "8")),
    pool_reset_session=True,
    **DB_CONFIG,
)


def get_connection():
    return pool.get_connection()
