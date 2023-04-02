#!/usr/bin/env python3

import logging
import queue
import socket
import socketserver
import threading
import time
from collections import namedtuple

from netflow.utils import UnknownExportVersion, parse_packet
from netflow.v9 import V9TemplateNotRecognized
from netflow.ipfix import IPFIXTemplateNotRecognized

RawPacket = namedtuple('RawPacket', ['ts', 'client', 'data'])
ParsedPacket = namedtuple('ParsedPacket', ['ts', 'client', 'export'])

PACKET_TIMEOUT = 60 * 60

class QueuingRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]  # get content, [1] would be the socket
        self.server.queue.put(RawPacket(time.time(), self.client_address, data))
        logging.debug("Received {} bytes of data from {}".format(len(data), self.client_address))


class QueuingUDPListener(socketserver.ThreadingUDPServer):
    def __init__(self, interface, queue):
        self.queue = queue

        if ":" in interface[0]:
            self.address_family = socket.AF_INET6

        super().__init__(interface, QueuingRequestHandler)


class ThreadedNetFlowListener(threading.Thread):
    def __init__(self, host: str, port: int):
        self.output = queue.Queue()
        self.input = queue.Queue()
        self.host = host
        self.port = port
        self.server = QueuingUDPListener((host, port), self.input)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self._shutdown = threading.Event()
        super().__init__()

    def get(self, block=True, timeout=None) -> ParsedPacket:
        return self.output.get(block, timeout)

    def run(self):
        logging.info("NetFlow listener started on {}:{}".format(self.host, self.port))
        try:
            templates = {"netflow": {}, "ipfix": {}}
            to_retry = []
            while not self._shutdown.is_set():
                try:
                    pkt = self.input.get(block=True, timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    export = parse_packet(pkt.data, templates)
                except UnknownExportVersion as e:
                    logging.error("{}, ignoring the packet".format(e))
                    continue
                except (V9TemplateNotRecognized, IPFIXTemplateNotRecognized):
                    if time.time() - pkt.ts > PACKET_TIMEOUT:
                        logging.warning("Dropping an old and undecodable v9 ExportPacket")
                    else:
                        to_retry.append(pkt)
                        logging.debug("Failed to decode a v9 ExportPacket - will re-attempt when a new template is discovered")
                    continue

                if export.header.version == 10:
                    logging.debug("Processed an IPFIX ExportPacket with length {}.".format(export.header.length))
                else:
                    logging.debug("Processed a v{} ExportPacket with {} flows.".format(export.header.version, export.header.count))

                # If any new templates were discovered, dump the unprocessable data back into the queue and try to decode them again
                if export.header.version in [9, 10] and export.contains_new_templates and to_retry:
                    logging.debug("Received new template(s)")
                    logging.debug("Will re-attempt to decode {} old v9 ExportPackets".format(len(to_retry)))
                    for p in to_retry:
                        self.input.put(p)
                    to_retry.clear()

                self.output.put(ParsedPacket(pkt.ts, pkt.client, export))

            logging.info("Netflow listener stopped")
        finally:
            self.server.shutdown()
            self.server.server_close()

    def stop(self):
        #logging.info("Shuttdown netflow listener")
        self._shutdown.set()

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)
        super().join(timeout=timeout)
