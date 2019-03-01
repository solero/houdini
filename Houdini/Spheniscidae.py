from Houdini import Handlers
from Houdini.Handlers import XMLPacket, XTPacket

from asyncio import IncompleteReadError

import defusedxml.cElementTree as Et
from xml.etree.cElementTree import Element, SubElement, tostring


class Spheniscidae:

    __slots__ = ['__reader', '__writer', 'server', 'logger',
                 'peer_name', 'received_packets', 'joined_world']

    Delimiter = b'\x00'

    def __init__(self, server, reader, writer):
        self.__reader = reader
        self.__writer = writer

        self.server = server
        self.logger = server.logger

        self.peer_name = writer.get_extra_info('peername')
        self.server.peers_by_ip[self.peer_name] = self

        self.joined_world = False

        self.received_packets = set()

    async def send_error_and_disconnect(self, error):
        await self.send_xt('e', error)
        await self.close()

    async def send_error(self, error):
        await self.send_xt('e', error)

    async def send_policy_file(self):
        await self.send_line('<cross-domain-policy><allow-access-from domain="*" to-ports="{}" /></cross-domain-policy>'
                             .format(self.server.server_config['Port']))
        await self.close()

    async def send_xt(self, *data):
        data = list(data)

        handler_id = data.pop(0)
        internal_id = -1

        mapped_data = map(str, data)

        xt_data = '%'.join(mapped_data)
        line = '%xt%{0}%{1}%{2}%'.format(handler_id, internal_id, xt_data)
        await self.send_line(line)

    async def send_xml(self, xml_dict):
        data_root = Element('msg')
        data_root.set('t', 'sys')

        sub_element_parent = data_root
        for sub_element, sub_element_attribute in xml_dict.iteritems():
            sub_element_object = SubElement(sub_element_parent, sub_element)

            if type(xml_dict[sub_element]) is dict:
                for sub_element_attribute_key, sub_element_attribute_value in xml_dict[sub_element].iteritems():
                    sub_element_object.set(sub_element_attribute_key, sub_element_attribute_value)
            else:
                sub_element_object.text = xml_dict[sub_element]

            sub_element_parent = sub_element_object

        xml_data = tostring(data_root)
        await self.send_line(xml_data)

    async def send_line(self, data):
        self.logger.debug('Outgoing data: %s', data)
        self.__writer.write(data.encode() + Spheniscidae.Delimiter)

    async def close(self):
        self.__writer.close()

    async def __handle_xt_data(self, data):
        self.logger.debug("Received XT data: {0}".format(data))
        parsed_data = data.split("%")[1:-1]

        packet_id = parsed_data[2]
        packet = XTPacket(packet_id)

        if Handlers.listener_exists(self.server.xt_listeners, self.server.xml_listeners, packet):
            xt_listeners = self.server.xt_listeners[packet]
            packet_data = parsed_data[4:]

            for listener in xt_listeners:
                await listener(self, packet_data)
            self.received_packets.add(packet)
        else:
            self.logger.debug("Handler for {0} doesn't exist!".format(packet_id))

    async def __handle_xml_data(self, data):
        self.logger.debug("Received XML data: {0}".format(data))

        element_tree = Et.fromstring(data)

        if element_tree.tag == "policy-file-request":
            await self.send_policy_file()

        elif element_tree.tag == "msg":
            self.logger.debug("Received valid XML data")

            try:
                body_tag = element_tree[0]
                action = body_tag.get("action")
                packet = XMLPacket(action)

                if Handlers.listener_exists(self.server.xt_listeners, self.server.xml_listeners, packet):
                    xml_listeners = self.server.xml_listeners[packet]

                    for listener in xml_listeners:
                        await listener(self, body_tag)

                    self.received_packets.add(packet)
                else:
                    self.logger.warn("Packet did not contain a valid action attribute!")

            except IndexError:
                self.logger.warn("Received invalid XML data (didn't contain a body tag)")
        else:
            self.logger.warn("Received invalid XML data!")

    async def __client_connected(self):
        self.logger.info('Client %s connected', self.peer_name)

    async def __client_disconnected(self):
        del self.server.peers_by_ip[self.peer_name]

        self.logger.info('Client %s disconnected', self.peer_name)

    async def __data_received(self, data):
        data = data.decode()[:-1]
        if data.startswith('<'):
            await self.__handle_xml_data(data)
        else:
            await self.__handle_xt_data(data)

    async def run(self):
        await self.__client_connected()
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
            except ConnectionResetError:
                self.__writer.close()
        await self.__client_disconnected()
