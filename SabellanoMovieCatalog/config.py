import os

class Config:
    SECRET_KEY = os.environ.get('123') or '123'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'movie_catalog'
