import asyncio
import sys
from houdini.houdini import HoudiniFactory

if __name__ == '__main__':
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    factory_instance = HoudiniFactory(server='Login')
    asyncio.run(factory_instance.start())
