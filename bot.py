import sqlite3
import pprint
import xpresser
import os
import inspect
from config import DTSkypeBotConfig
from time import sleep
from libs.pythondaemon.daemon import Daemon
from message import MessageHandler

class DTSkypeBot(Daemon):

    is_launched = False
    is_authenticated = False

    def __init__(self, pidfile, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.', umask=022, verbose=1):

        super(DTSkypeBot, self).__init__(pidfile, stdin, stdout, stderr, home_dir, umask, verbose)

        self.login      = DTSkypeBotConfig.login
        self.password   = DTSkypeBotConfig.password
        self.sdb_path   = os.path.expanduser("~") + "/.Skype/" + self.login + "/main.db"

        resource_path   = os.path.dirname(inspect.getsourcefile(lambda _: None)) + "/resources"
        self.db_path    = resource_path + "/chats.db"

        self.xpress     = xpresser.Xpresser()
        self.xpress.load_images(resource_path)

    def connect(self):
        self.skypedb  = sqlite3.connect(self.sdb_path)
        self.botdb    = sqlite3.connect(self.db_path)
        return False

    def authenticate(self):
        print "Authentication started"
        if not self.is_launched:
            self.launch()

        try:
            self.xpress.wait('skype-loginbox')
            self.xpress.click('skype-loginbox')
            self.xpress.double_click('login')
            self.xpress.type(self.login)

            self.xpress.click('password')
            self.xpress.type(self.password)
        except xpresser.xp.ImageNotFound:
            self.is_authenticated = False

        # Maybe we already have everythiig? Let's try to login and check for errors
        self.xpress.click('skype-sign_in')

        try:
            self.xpress.wait('skype-window_top')
            self.is_authenticated = True
            # establishing connection to sqlite
            self.connect()

        except xpresser.xp.ImageNotFound:
            return False

    def wait_incoming(self):

        botdb_cursor = self.botdb.cursor()
        botdb_cursor.execute("SELECT * FROM config")
        config_data = botdb_cursor.fetchone()
        botdb_cursor.close()

        lastid = (config_data[0], )
        skypedb_cursor = self.skypedb.cursor()
        skypedb_cursor.execute("SELECT convo_id, body_xml, id, timestamp, author FROM messages WHERE id > ? ORDER BY id ASC", lastid)
        messages = skypedb_cursor.fetchall()
        skypedb_cursor.close()

        if not messages:
            return False

        for message in messages:
            if message[4] == DTSkypeBotConfig.login:
                print "Ignoring messages from ourselves"
                continue
            MessageHandler(self, message[0], message[1])

        last_message = [message[2], message[3]]

        botdb_cursor = self.botdb.cursor()
        botdb_cursor.execute("UPDATE config SET last_message_id = ?, last_message_timestamp = ?", last_message)
        self.botdb.commit()

    def chat_register(self, data):
        self.send_message({'blob': data['blob'], 'message': '/get blob'})
        chat_id = None

        botdb_cursor = self.botdb.cursor()
        botdb_cursor.execute("SELECT * FROM config")
        config_data = botdb_cursor.fetchone()

        while chat_id is None:

            lastid = (config_data[0], )
            skypedb_cursor = self.skypedb.cursor()
            skypedb_cursor.execute("SELECT convo_id, body_xml, id, timestamp FROM messages WHERE id > ? AND body_xml like 'blob=%' ORDER BY id DESC", lastid)
            message = skypedb_cursor.fetchone()
            skypedb_cursor.close()
            if message is not None:
                chat_id = message[0]
                break

            sleep(0.5)

        blob = message[1].split("=")[1]

        chat = [message[0], blob]

        botdb_cursor.execute("INSERT INTO chats(chat_id, chat_blob) values (?,?)", chat)
        self.botdb.commit()
        botdb_cursor.close()
        print "Chat with blob %s and id %s registered." % (blob, message[1])

    def chat_drop(self, data):
        self.botdb = sqlite3.connect(self.db_path)

        id = (data['blob'], )
        botdb_cursor = self.botdb.cursor();
        botdb_cursor.execute("SELECT * FROM chats WHERE blob=?", id)
        chat = botdb_cursor.fetchone()

        self.send_message({'blob': chat[2], 'message': '/leave'})
        botdb_cursor.execute("DELETE FROM chats WHERE id = ?", (chat[0], ))
        self.botdb.commit()

        print "Chat with blob %s and id %d dropped." % (chat[2], chat[0])

        return False

    def chat_info(self, data):
        return False

    def send_message(self, data):
        pprint.pprint(data)

        if 'blob' not in data:
            self.botdb = sqlite3.connect(self.db_path)
            id = (data['chat_id'], )
            botdb_cursor = self.botdb.cursor();
            botdb_cursor.execute("SELECT * FROM chats WHERE chat_id=?", id)
            chat = botdb_cursor.fetchone()
        else:
            chat = [0, 0, data['blob']]

        if chat is None:
            print 'Chat not registered'
            return False

        try:
            try:
                search_input = self.xpress.find('search_clear', 0.1)
                self.xpress.click(search_input.x + 5, search_input.y + 5)

            except xpresser.xp.ImageNotFound:
                print 'Search clear button not found'

            search_input = self.xpress.find('search-contacts',  0.1)
            self.xpress.click(search_input.x + 10, search_input.y + 10)
            self.xpress.click('skype-join_chat')

        except xpresser.xp.ImageNotFound:
            print 'Contacts search not found'

        try:
            self.xpress.wait('skype-mark_viewed', 0.1)
            self.xpress.click('skype-mark_viewed')
        except xpresser.xp.ImageNotFound:
            print 'Mark viewed not found'

        search_input = self.xpress.find('search-chats')
        self.xpress.click(search_input.x + 40, search_input.y + 10)
        self.xpress.type([chat[2],"<Enter>"])
        self.xpress.click('skype-message_field')
        self.xpress.type([data['message'], "<Enter>"])

        closedown = self.xpress.find('chat_close', 1)
        self.xpress.click(closedown.x+8, closedown.y+8)

        try:
            search_input = self.xpress.find('search_clear', 0.1)
            self.xpress.click(search_input.x + 5, search_input.y + 5)
            self.xpress.click(search_input.x - 50, search_input.y - 50)

        except xpresser.xp.ImageNotFound:
            print 'Search clear button not found'

    def launch(self):
        print "Skype launching"
        self.xpress.click('skype-launch-icon')
        self.is_launched = True

    def quit(self):
        self.xpress.wait('skype-window_top')
        window_top = self.xpress.find('skype-top_menu')

        self.xpress.click('skype-top_menu')

        #waiting for effects
        sleep(1)

        self.xpress.click(window_top.x + 20, window_top.y + 320)

        try:
            self.xpress.find('skype-top_menu')
        except xpresser.xp.ImageNotFound:
            return True
