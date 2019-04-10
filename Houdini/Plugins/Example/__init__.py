from Houdini import Handlers
from Houdini.Handlers import XTPacket

from Houdini.Plugins import IPlugin


class Example(IPlugin):
    author = "Ben"
    description = "Example plugin for developers"
    version = "1.0.0"

    def __init__(self, server):
        self.server = server

    async def ready(self):
        self.server.logger.info('Example.ready()')

    async def message_cooling(self, p):
        print("{}, Message was sent during cooldown".format(p))

    @Handlers.handler(XTPacket('s', 'sm'))
    @Handlers.cooldown(1, callback=message_cooling)
    async def handle_send_message(self, p, message: str):
        print('Do stuff with {}'.format(message))

    # @Commands.command('ping')
    async def ping(self, p):
        p.send_xt('cprompt', 'Pong')

    # @Events.on('connected')
    async def on_connected(self, client):
        print(client)

    # @Events.on('disconnected')
    async def on_disconnect(self, client):
        print(client)

