import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Load environment variables from .env file
base_dir = Path(__file__).resolve().parent
env_path = base_dir / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-community-help-connect-2026')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Database connection parameters
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'tasmia@737305')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'community_help_db')
    
    # Check for direct database URL override or fallback
    USE_SQLITE_FALLBACK = os.getenv('USE_SQLITE_FALLBACK', '0').lower() in ('1', 'true', 'yes')
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    elif USE_SQLITE_FALLBACK:
        sqlite_db = base_dir / 'instance' / 'community_help.db'
        sqlite_db.parent.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{sqlite_db}'
    else:
        # Standard MySQL PyMySQL URI
        SQLALCHEMY_DATABASE_URI = URL.create(
            drivername="mysql+pymysql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
            query={"charset": "utf8mb4"},
            )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with in-memory database and disabled CSRF for automated tests."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SQLALCHEMY_SESSION_OPTIONS = {'expire_on_commit': False}


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS in production


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
