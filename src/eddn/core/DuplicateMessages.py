# coding: utf8
import hashlib
import re
import simplejson
import zlib

from datetime import datetime, timedelta
from eddn.conf.Settings import Settings
from threading import Lock, Thread
from time import sleep


class DuplicateMessages(Thread):
    max_minutes = Settings.RELAY_DUPLICATE_MAX_MINUTES

    caches = {}

    lock = Lock()

    def __init__(self):
        super(DuplicateMessages, self).__init__()
        self.daemon = True

    def run(self):
        while True:
            sleep(60)
            with self.lock:
                maxTime = datetime.utcnow()

                for key in self.caches.keys():
                    if self.caches[key] + timedelta(minutes=self.max_minutes) < maxTime:
                        del self.caches[key]

    def isDuplicated(self, message):
        with self.lock:
            message = zlib.decompress(message)
            message = simplejson.loads(message)

            # Test messages are not duplicate
            if re.search('test', message['$schemaRef'], re.I):
                return False

            if message['header']['gatewayTimestamp']:
                del message['header']['gatewayTimestamp']  # Prevent dupe with new timestamp ^^
            if message['message']['timestamp']:
                del message['message']['timestamp']  # Prevent dupe with new timestamp ^^

            message = simplejson.dumps(message)
            key = hashlib.sha256(message).hexdigest()

            if key not in self.caches:
                self.caches[key] = datetime.utcnow()
                return False
            else:
                self.caches[key] = datetime.utcnow()
                return True
