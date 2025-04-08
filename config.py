import os
from dotenv import load_dotenv

# Carrega as variáveis do .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN não definido. Configure no arquivo .env ou como variável de ambiente.")

    # Steam
    STEAM_API_KEY = os.getenv('STEAM_API_KEY')
    if not STEAM_API_KEY:
        raise ValueError("STEAM_API_KEY não definido. Configure no arquivo .env ou como variável de ambiente.")
    
    # Database
    DATABASE_NAME = 'steam_bot.db'
    
    # Update settings
    DEFAULT_CHECK_INTERVAL = 6  # hours
    MAX_CHECK_INTERVAL = 24
    MIN_CHECK_INTERVAL = 1
    
    # Cache
    CACHE_EXPIRATION = 3600  # 1 hour in seconds
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'steam_bot.log'
