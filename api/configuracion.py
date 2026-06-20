import os 

class Configuracion:
    """ Clase de configuración para la aplicación. """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # API 
    API_KEY = os.environ.get('API_KEY', 'my_api_key')

    # RATIO DE TIEMPO LIMITE 
    RATIO_TIEMPO_LIMITE = '100 por hora'

    # Telegram — se leen de variables de entorno (véase .env.example)
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

class DevelopmentConfig(Configuracion):
    """ Configuración específica para el entorno de desarrollo. """

class productionConfig(Configuracion):
    """ Configuración específica para el entorno de producción. """

class testingConfig(Configuracion):
    """ Configuración específica para el entorno de pruebas. """

# Diccionario de configuraciones para facilitar la selección del entorno
config = {
    'development': DevelopmentConfig,
    'production': productionConfig,
    'testing': testingConfig,
    'default': DevelopmentConfig
}