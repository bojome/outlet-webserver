#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from urllib.parse import parse_qs
from http.server import HTTPServer, SimpleHTTPRequestHandler
from Devices import DeviceManager
import json
import argparse
from distutils.util import strtobool

parser = argparse.ArgumentParser(description='Run the RF Device Manager as Webserver')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--database', type=argparse.FileType('r'),
                   help='The device database')
parser.add_argument('--port', '-p', type=int, default=8000,
                    help='The web server is run on this port number')
args = parser.parse_args()

if args.database:
    dm = DeviceManager(args.database.name)
else:
    raise ValueError('An input argument was not specified. \
                     This should\'ve been catched by argparse')



class MyRequestHandler (SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith('/?'):
            data = parse_qs(self.path[2:])

            querystring = self.path[2:]

            if "addDevice" in querystring:
                if (('housecode' in data) and ('devicecode' in data)
                    and ('description' in data) and ('status' in data)):
                    conversionError = False
                    try:
                        status=strtobool(data['status'][0])
                    except:
                        r = json.dumps({
                            'Error' : 'Parsing status'
                        })
                        conversionError = True

                    if not conversionError:
                        o = dm.addDevice(data['housecode'][0], data['devicecode'][0],
                                         data['description'][0].strip(), status)
                        r = json.dumps(o)
                else:
                    print(data)
                    r = json.dumps('Error')
            elif "statusDevices" in querystring:
                devices = dm.statusDevices()
                r = json.dumps(devices)
            elif "switchDevice" in querystring:
                if ('housecode' in data) and ('devicecode' in data) and ('status' in data):
                    conversionError = False
                    try:
                        status=strtobool(data['status'][0])
                    except:
                        r = json.dumps({'Error':'Parsing status'})
                        conversionError = True

                    if not conversionError:
                        o = dm.switchDeviceStatus(data['housecode'][0], data['devicecode'][0], status)
                        r = json.dumps(o)
                else:
                    r = json.dumps('Error')
            else:
                r = json.dumps('Error')

            self.send_response(200)
            self.send_header("Content-type", "application/json;charset=utf-8")
            self.send_header("Content-length", len(r))
            self.end_headers()
            self.wfile.write(r.encode("utf-8"))
            return

        return super().do_GET()


httpd = HTTPServer(('', args.port), MyRequestHandler)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print()
    sys.exit(0)
finally:
    dm.close()
