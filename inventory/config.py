import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database configuration
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.getenv('DATABASE_PORT', 32000))
    DATABASE_USER = os.getenv('DATABASE_USER', 'root')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'root')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'inventory_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    
    # Service URLs
    PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product:5000')
    
    # Service configuration
    SERVICE_NAME = 'inventory'
    SERVICE_PORT = 5006
    LOW_STOCK_THRESHOLD = 10
