from asyncio import CancelledError, IncompleteReadError, LimitOverrunError
from xml.etree.cElementTree import Element, SubElement, tostring

import defusedxml.cElementTree as Et

from houdini.constants import ClientType
from houdini.handlers import AuthorityError, AbortHandlerChain, XMLPacket, XTPacket


class Spheniscidae:

    __slots__ = ['__reader', '__writer', 'server', 'logger',
                 'peer_name', 'received_packets', 'joined_world',
                 'client_type']

    Delimiter = b'\x00'

    def __init__(self, server, reader, writer):
        self.__reader = reader
        self.__writer = writer

        self.server = server
        self.logger = server.logger

        self.peer_name = writer.get_extra_info('peername')
        self.server.peers_by_ip[self.peer_name] = self

        self.joined_world = False
        self.client_type = None

        self.received_packets = set()

        super().__init__()

    @property
    def is_vanilla_client(self):
        return self.client_type == ClientType.Vanilla

    @property
    def is_legacy_client(self):
        return self.client_type == ClientType.Legacy

    async def send_error_and_disconnect(self, error, *args):
        await self.send_xt('e', error, *args)
        await self.close()

    async def send_error(self, error, *args):
        await self.send_xt('e', error, *args)

    async def send_policy_file(self):
        await self.send_line(f'<cross-domain-policy><allow-access-from domain="*" to-ports="'
                             f'{self.server.config.port}" /></cross-domain-policy>')
        await self.close()

    async def send_xt(self, handler_id, *data):
        internal_id = -1

        xt_data = '%'.join(str(d) for d in data)
        line = f'%xt%{handler_id}%{internal_id}%{xt_data}%'
        await self.send_line(line)

    async def send_xml(self, xml_dict):
        data_root = Element('msg')
        data_root.set('t', 'sys')

        sub_element_parent = data_root
        for sub_element, sub_element_attribute in xml_dict.items():
            sub_element_object = SubElement(sub_element_parent, sub_element)

            if type(xml_dict[sub_element]) is dict:
                for sub_element_attribute_key, sub_element_attribute_value in xml_dict[sub_element].items():
                    sub_element_object.set(sub_element_attribute_key, sub_element_attribute_value)
            else:
                sub_element_object.text = xml_dict[sub_element]

            sub_element_parent = sub_element_object

        xml_data = tostring(data_root)
        await self.send_line(xml_data.decode('utf-8'))

    async def send_line(self, data):
        if not self.__writer.is_closing():
            self.logger.debug(f'Outgoing data: {data}')
            self.__writer.write(data.encode('utf-8') + Spheniscidae.Delimiter)

    async def close(self):
        self.__writer.close()

        await self._client_disconnected()

    async def __handle_xt_data(self, data):
        self.logger.debug(f'Received XT data: {data}')
        parsed_data = data.split('%')[1:-1]

        packet_id = parsed_data[2]
        packet = XTPacket(packet_id, ext=parsed_data[1])

        if packet in self.server.xt_listeners:
            xt_listeners = self.server.xt_listeners[packet]
            packet_data = parsed_data[4:]

            for listener in xt_listeners:
                if not self.__writer.is_closing() and listener.client_type is None \
                        or listener.client_type == self.client_type:
                    await listener(self, packet_data)
            self.received_packets.add(packet)
        else:
            self.logger.warn('Handler for %s doesn\'t exist!', packet_id)

    async def __handle_xml_data(self, data):
        self.logger.debug(f'Received XML data: {data}')

        element_tree = Et.fromstring(data)

        if element_tree.tag == 'policy-file-request':
            await self.send_policy_file()

        elif element_tree.tag == 'msg':
            self.logger.debug('Received valid XML data')

            try:
                body_tag = element_tree[0]
                action = body_tag.get('action')
                packet = XMLPacket(action)

                if packet in self.server.xml_listeners:
                    xml_listeners = self.server.xml_listeners[packet]

                    for listener in xml_listeners:
                        if not self.__writer.is_closing() and listener.client_type is None \
                                or listener.client_type == self.client_type:
                            await listener(self, body_tag)

                    self.received_packets.add(packet)
                else:
                    self.logger.warn('Packet did not contain a valid action attribute!')

            except IndexError:
                self.logger.warn('Received invalid XML data (didn\'t contain a body tag)')
        else:
            self.logger.warn('Received invalid XML data!')

    async def _client_connected(self):
        self.logger.info(f'Client {self.peer_name} connected')

        await self.server.dummy_event_listeners.fire('connected', self)

    async def _client_disconnected(self):
        if self.peer_name in self.server.peers_by_ip:
            del self.server.peers_by_ip[self.peer_name]
            self.logger.info(f'Client {self.peer_name} disconnected')

            await self.server.dummy_event_listeners.fire('disconnected', self)

    async def __data_received(self, data):
        data = data.decode()[:-1]
        try:
            if data.startswith('<'):
                await self.__handle_xml_data(data)
            else:
                await self.__handle_xt_data(data)
        except AuthorityError:
            self.logger.debug(f'{self} tried to send game packet before authentication')
        except AbortHandlerChain as e:
            self.logger.info(f'Handler chain aborted: {str(e)}')

    async def run(self):
        await self._client_connected()
        while not self.__writer.is_closing():
            try:
                data = await self.__reader.readuntil(
                    separator=Spheniscidae.Delimiter)
                if data:
                    await self.__data_received(data)
                else:
                    self.__writer.close()
                await self.__writer.drain()
            except IncompleteReadError:
                self.__writer.close()
            except CancelledError:
                self.__writer.close()
            except ConnectionResetError:
                self.__writer.close()
            except LimitOverrunError:
                self.__writer.close()
            except BaseException as e:
                self.logger.exception(e.__traceback__)

        await self._client_disconnected()

    def __repr__(self):
        return f'<Spheniscidae {self.peer_name}>'
