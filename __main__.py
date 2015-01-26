# Example package with a console entry point
from server import Server

bot = Server("/tmp/dtskypebot.pid")
bot.run()
