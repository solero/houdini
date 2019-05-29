import asyncio
import sys
import logging
from houdini.houdini import HoudiniFactory

if __name__ == '__main__':
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    logger = logging.getLogger('houdini')
    factory_instance = HoudiniFactory(server='Login')
    try:
        asyncio.run(factory_instance.start())
    except KeyboardInterrupt:
        logger.info('Shutting down...')
