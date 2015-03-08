import json
from flask import Flask, make_response
from flask.ext.restful import Api

from src import settings, utils
from src.models import db

__version__ = '0.0.1'

app = Flask(__name__,
            template_folder=settings.STATIC_ASSETS_PATH,
            static_folder=settings.STATIC_ASSETS_PATH,
            static_path='/static')

api = Api(app)

# configure our database
settings.DATABASE_CONFIG.update({'threadlocals': True})
app.config['DATABASE'] = settings.DATABASE_CONFIG
db.init_app(app)


@api.representation('application/json')
def json_representation(data, code, headers=None):
    resp = make_response(json.dumps(data, cls=utils.JSONEncoder), code)
    resp.headers.extend(headers or {})
    return resp


from src import controllers