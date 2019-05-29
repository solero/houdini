from houdini import handlers
from houdini.handlers import XTPacket

from houdini.plugins import IPlugin
from houdini import commands

from houdini import permissions


class Example(IPlugin):
    author = "Ben"
    description = "Example plugin for developers"
    version = "1.0.0"

    def __init__(self, server):
        super().__init__(server)

    async def ready(self):
        self.server.logger.info('Example.ready()')
        await self.server.permissions.register('houdini.ping')

    async def message_cooling(self, p):
        print("{}, Message was sent during cooldown".format(p))

    @handlers.handler(XTPacket('m', 'sm'))
    @handlers.cooldown(1, callback=message_cooling)
    async def handle_send_message(self, p, message: str):
        print('Do stuff with {}'.format(message))

    @commands.command('ping')
    @permissions.has('houdini.ping')
    async def ping(self, p):
        p.send_xt('cprompt', 'Pong')
