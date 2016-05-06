#coding:utf-8

import logging
import os
import re
import sys
import socket
from urlparse import urlparse
import pprint
import urllib  
import motor.motor_tornado
import datetime
import simplejson

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
from tornado import gen

client = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = client.error_store
collection = db.error_url

class uriHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
    	pprint.pprint(self.request.body)
        try:
            uri = self.get_body_argument("uri")
            if not uri:
            	out = {"status":250,"message":"uri is null"}
            	self.write(out)
            	self.finish()
            	return
        except Exception as e:
            out = {"status":249,"message":"Exception Occurs"}
            pprint.pprint(e)
            self.write(out)
            self.finish()
            return

        data = {"uri":uri}
        data_send = urllib.urlencode(data)
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield client.fetch('http://127.0.0.1:8555/chromedriver',method='POST',body=data_send)

        json_body = simplejson.loads(response.body)

        self.write(json_body)
        self.finish()

class resultHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        referer = self.get_query_argument('referer')
        pprint.pprint(referer);
        cursor = collection.find({"referer":referer})
        out_list = []
        while (yield cursor.fetch_next):
            document = cursor.next_object()
            out = {"referer":document['referer'],"errorURL":document['uri']}
            out_list.append(out)


        if out_list is None:
            body = {"status":440,"message":"cannot find the referer record"}

        else:
            body = {"status":200,"list":out_list}

        self.write(body)
        self.finish()


if __name__ == '__main__':
	application = tornado.web.Application([
		(r"/uri",uriHandler),
		(r"/result",resultHandler)
		])
	application.listen(7999)
	tornado.ioloop.IOLoop.current().start()
