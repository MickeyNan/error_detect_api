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



def HandleReferer(referer):
	questionmarkpos = referer.find('?')
	if (questionmarkpos > 0):
		referer = referer[0:questionmarkpos]
	if (referer.endswith('/')):
		referer = referer[0:-1]
	if (referer.find('http://') == 0):
		referer = referer[7:]
	return referer


def AsyncFetch(req):
	client = tornado.httpclient.AsyncHTTPClient()
	future = client.fetch(req)
	IOLoop.current().add_future(future)
	result = yield future
	raise gen.Return(result.body)


class ProxyHandler(tornado.web.RequestHandler):
	@tornado.gen.coroutine
	def get(self):


		def handle_response(response):
			if (response.error and not isinstance(response.error,tornado.httpclient.HTTPError)):
				self.set_status(500)
				self.write('Internal server error:\n' + str(response.error))
			else:
				self.set_status(response.code)
				for header in ('Date', 'Cache-Control', 'Server','Content-Type', 'Location'):
					v = response.headers.get(header)
					if v:
						self.set_header(header, v)

				v = response.headers.get_list('Set-Cookie')
				if v:
					for i in v:
						self.add_header('Set-Cookie',i)
				self.add_header('Via','proxy')
				if response.body:
					self.write(response.body)
			self.finish()


		url = self.request.uri

		body = self.request.body
		if not body:
			body = None

		req = tornado.httpclient.HTTPRequest(
			url, method=self.request.method,body=body,
			headers=self.request.headers,follow_redirects=False,allow_nonstandard_methods=True)


		try:

			client = tornado.httpclient.AsyncHTTPClient()
			future = client.fetch(req)
			#tornado.ioloop.IOLoop.current().add_future(future,lambda x:x)
			result = yield future
			handle_response(result)

		except tornado.httpclient.HTTPError as e:
			if hasattr(e, 'response') and e.response:
				handle_response(e.response)
			
			try:
				error_pos = e.response.headers['Location'].find('error')
				four_zero_four_pos = e.response.headers['Location'].find('404')
				if (error_pos > 0 or four_zero_four_pos > 0):
					now = datetime.datetime.utcnow()
					referer = HandleReferer(url)
					if (yield collection.find_one({'uri':self.request.uri})):
						pass
					else:
						document = {"uri":self.request.uri,"referer":referer,"createdAt":now}
						yield collection.save(document)		
					
			except Exception as noLocation:
				pprint.pprint(noLocation)

			if (e.code == 404):
				try:
					referer = self.request.headers['Referer']
				except Exception as referer_error:
					referer = self.request.uri

				if (yield collection.find_one({'uri':self.request.uri})):
					pass
				else:
					referer = HandleReferer(referer)
					now = datetime.datetime.utcnow()
					document = {"uri":self.request.uri,"referer":referer,"createdAt":now}
					yield collection.save(document)

	@tornado.web.asynchronous
	def post(self):
		return self.get()


if __name__ == '__main__':
	application = tornado.web.Application([
		(r".*",ProxyHandler),
		])
	application.listen(8000)
	tornado.ioloop.IOLoop.current().start()

