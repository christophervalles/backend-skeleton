"""
Flask-restful based API implementation for app.

Currently the Flask server is used to serve the static assets (and the Angular.js app),
but this is only due to configuration issues and temporary.
"""
from flask import send_from_directory, request
from flask.ext.restful import Resource, abort

from src import statsd_client, models, settings
from src.wsgi import app, api
from src.tasks import record_event


@app.route('/ping', methods=['GET'])
def ping():
    return 'PONG.'


class BaseResource(Resource):
    # decorators = [auth.required]

    def __init__(self, *args, **kwargs):
        super(BaseResource, self).__init__(*args, **kwargs)
        self._user = None

    @property
    # def current_user(self):
    #     return current_user._get_current_object()

    def dispatch_request(self, *args, **kwargs):
        with statsd_client.timer('requests.{}.{}'.format(request.endpoint, request.method.lower())):
            response = super(BaseResource, self).dispatch_request(*args, **kwargs)
        return response


class EventAPI(BaseResource):
    def post(self):
        events_list = request.get_json(force=True)
        for event in events_list:
            record_event.delay(event)


api.add_resource(EventAPI, '/api/events', endpoint='events')


class UserListAPI(BaseResource):
    def get(self, field='', offset=0, search=None):
        if field.strip('-') in models.User.mapping.keys():
            model_field = models.User.mapping[field.strip('-')]

        results = models.User.all().limit(250).offset(offset)
        total = models.User.all()

        if field[0:1] == '-':
            results = results.order_by(getattr(models.User, model_field).desc())
        else:
            results = results.order_by(getattr(models.User, model_field))

        if search:
            if search.isdigit():
                results = results.where((models.User.id == search) | (models.User.userName.contains(search)))
                total = total.where((models.User.id == search) | (models.User.userName.contains(search)))
            else:
                results = results.where(models.User.userName.contains(search))
                total = total.where(models.User.userName.contains(search))

        users = [u.to_dict() for u in results]
        return {
            'users': users,
            'total': total.count()
        }


class UserAPI(BaseResource):
    def get(self, user_id):
        u = models.User.get(models.User.id == user_id)
        if u:
            return u.to_dict()
        else:
            abort(404, message="User not found.")


api.add_resource(
    UserListAPI,
    '/api/users',
    '/api/users/order/<field>',
    '/api/users/order/<field>/offset/<offset>',
    '/api/users/order/<field>/offset/<offset>/search/',
    '/api/users/order/<field>/offset/<offset>/search/<search>',
    endpoint='users'
)
api.add_resource(UserAPI, '/api/users/<user_id>', endpoint='user')


@app.route('/<path:filename>')
def send_static(filename):
    return send_from_directory(settings.STATIC_ASSETS_PATH, filename)


if __name__ == '__main__':
    app.run(debug=True)



