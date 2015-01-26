import os
from constants import *
from libs.beanstalkc import beanstalkc
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound

import json

class APIChild():
    def __init__(self, config):
        self.beanstalk = beanstalkc.Connection(host=config['beanstalk_host'], port=config['beanstalk_port'])

        self.url_map = Map([
            Rule('/', endpoint='status'),
            Rule('/stop', endpoint='stop_server'),
            Rule('/chat_registration', endpoint='chat_registration'),
            Rule('/chat_info', endpoint='chat_info'),
            Rule('/chat_drop', endpoint='chat_drop'),
            Rule('/send', endpoint='message')
        ])

    def dispatch_request(self, request):
        return Response('Hello World!')

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e

    #TODO implement server status
    def on_status(self, request):
        return Response(json.dumps({'status': RESPONSE_STATUS_SUCCESS,
                                    'message': 'some status info will be implemented here'}))

    def on_stop_server(self, request):
        self.beanstalk.put(json.dumps({'command':'stop'}))
        return Response(json.dumps({'status': RESPONSE_STATUS_SUCCESS, 'message': 'stop command pushed to server'}))

    def on_chat_registration(self, request):
        if request.args.get('blob') is None:
            return Response(json.dumps({'status': RESPONSE_STATUS_FAIL, 'message': 'blob parameter not provided'}))
        else:
            chat_blob = request.args.get('blob')
            self.beanstalk.put(json.dumps({'command':'registration', 'blob': chat_blob}))
            return Response(json.dumps({'status': RESPONSE_STATUS_SUCCESS, 'message': 'chat registration command was pushed to server'}))

    def on_chat_info(self, request):
        return Response(json.dumps({'status': RESPONSE_STATUS_SUCCESS,
                                    'message': 'some chat info will be implemented here'}))

    def on_chat_drop(self, request):
        if request.args.get('blob') is None:
            return Response(json.dumps({'status': RESPONSE_STATUS_FAIL, 'message': 'blob parameter not provided'}))
        else:
            chat_blob = request.args.get('blob')
            self.beanstalk.put(json.dumps({'command':'drop', 'blob': chat_blob}))
            return Response(json.dumps({'status': RESPONSE_STATUS_SUCCESS, 'message': 'chat drop command was pushed to server'}))

    def on_message(self, request):
        if request.args.get('chat_id') is None or request.args.get('message') is None:
            return Response(json.dumps({'status': RESPONSE_STATUS_FAIL, 'message': 'chat_id or message parameters not provided'}))
        else:
            chat_id = request.args.get('chat_id')
            message = request.args.get('message')

        self.beanstalk.put(json.dumps({'command':'message', 'chat_id': chat_id, 'message': message}))
        return Response(json.dumps({'status': RESPONSE_STATUS_SUCCESS, 'message': 'send message command pushed to server'}))

def create_app(beanstalk_host='localhost', beanstalk_port=11300):
    app = APIChild({
        'beanstalk_host':       beanstalk_host,
        'beanstalk_port':       beanstalk_port
    })

    return app