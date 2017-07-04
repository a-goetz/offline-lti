import os
if 'HEROKU_ENV' in os.environ:
    import heroku_settings as settings
else:
    import settings


class Config(object):
    PYLTI_CONFIG = settings.PYLTI_CONFIG


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    PYLTI_CONFIG = settings.PYLTI_CONFIG


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    PYLTI_CONFIG = settings.PYLTI_CONFIG


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    PYLTI_CONFIG = settings.PYLTI_CONFIG

# DEFINE ADDITIONAL CONFIGS AS NEEDED
