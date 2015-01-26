from config import DTSkypeBotConfig
from libs.beanstalkc import beanstalkc
from werkzeug.serving import run_simple
from bot import DTSkypeBot
from time import sleep
from rest import *
import signal
import os
import json


class Server(DTSkypeBot):
    def run(self):

        self.child_pid = os.fork()
        print self.child_pid
        if(self.child_pid == 0):

            app = create_app(beanstalk_host=DTSkypeBotConfig.beanstalk_host,
                             beanstalk_port=DTSkypeBotConfig.beanstalk_port)

            run_simple(DTSkypeBotConfig.api_http_host,
                       DTSkypeBotConfig.api_http_port,
                       app,
                       use_debugger=True,
                       use_reloader=False)

        else:
            pids = (os.getpid(), self.child_pid)
            print "parent: %d, child: %d" % pids
            self.runParent()

    def runParent(self):
        self.authenticate()
        self.beanstalk = beanstalkc.Connection(host=DTSkypeBotConfig.beanstalk_host, port=DTSkypeBotConfig.beanstalk_port)

        while True:
            job = self.beanstalk.reserve(1)

            if job:
                job_data = json.loads(job.body)
                job.delete()
                if(job_data['command'] == "stop"):
                    print "Stopping server and quitting Skype"
                    self.quit()
                    os.kill(self.child_pid, signal.SIGKILL)
                    os._exit(0)
                elif(job_data['command'] == "message"):
                    self.send_message(job_data)
                elif(job_data['command'] == "registration"):
                    self.chat_register(job_data)
                elif(job_data['command'] == "drop"):
                    self.chat_drop(job_data)
                elif(job_data['command'] == "info"):
                    self.chat_info(job_data)

            self.wait_incoming()
            sleep(1)
