import datetime
import os

SECRET_KEY = os.urandom(24)
SESSION_TYPE = "filesystem"

PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)
# deploy database
# HOST = "megamaxp.mysql.pythonanywhere-services.com"
# local database
HOST = "127.0.0.1"
PORT = 3306
USER = "megamaxp"
PASSWORD = "Aa123456!!"
DBNAME = "restaurant"
CHARSET = "utf8mb4"
