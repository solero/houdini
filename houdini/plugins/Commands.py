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
        print(f'hello')

    async def message_cooling(self, p):
        print(f'{p}, Message was sent during cooldown')

    @handlers.handler(XTPacket('m', 'sm'))
    @handlers.cooldown(1, callback=message_cooling)
    async def handle_send_message(self, p, penguin_id: int, message: str):
        print(f'Do stuff with {message}')

    @commands.command('ping')
    async def ping(self, p):
        await p.send_xt('cprompt', 'Pong')

    @commands.command('ac')
    async def add_coins(self, p, amount: int = 100):
        await p.add_coins(amount, stay=True)

    @commands.command('ai')
    async def add_inventory(self, p, item: int):
        await p.add_inventory(p.server.items[item], notify=True, cost=0)

    @commands.command('af')
    async def add_furniture(self, p, furniture: int):
        await p.add_furniture(p.server.furniture[furniture], notify=True, cost=0)
        
    @commands.command('jr')
    async def join_room(self, p, room_id: int):
        await p.join_room(p.server.rooms[room_id])