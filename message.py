import re
import urllib2
import json

class MessageHandler():

    callbacks = [
        'on_course',
        'on_echo',
        'on_boobs',
    ]

    def __init__(self, BotInstance, chat_id, message):
        if message is None:
            return

        self.bot_instance = BotInstance

        for callback in self.callbacks:
            if getattr(self, callback)(message):
                getattr(self, 'process_' + callback)(chat_id)

    def on_echo(self, message):
        return re.match('echo', message)

    def on_course(self, message):
        return re.match('rates|\$', message)

    def on_boobs(self, message):
        return re.match('boobs|boobies|tits', message)

    def process_on_echo(self, chat_id):
        self.bot_instance.send_message({'chat_id': chat_id, 'message': 'echo'})
        return False

    def process_on_boobs(self, chat_id):
        f = urllib2.urlopen('http://api.oboobs.ru/noise/1/')
        data = json.loads(f.read())
        self.bot_instance.send_message({'chat_id': chat_id,
                                        'message': "http://media.oboobs.ru/%s" % data[0][u'preview']})

        return False

    def process_on_course(self, chat_id):
        f = urllib2.urlopen('http://zenrus.ru/js/currents.js')
        data = json.loads(f.read().split("=")[1])
        self.bot_instance.send_message({'chat_id': chat_id,
                                        'message': u'USD: %.2f, EUR: %.2f, OIL: %.2f' % (data[0], data[1], data[2])})

        return False