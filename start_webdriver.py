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
import time

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
from tornado import gen
from selenium import webdriver

class startHandler(tornado.web.RequestHandler):
	@gen.coroutine
	def post(self):
		uri = self.get_body_argument("uri")
		if uri is None:
			out = {"status":250,"message":uri + " " + "is None"}
			self.write(out)
			self.finish()
		else:
			#代理设置为proxy.py的服务器
			PROXY = "127.0.0.1:8000"
			chrome_options = webdriver.ChromeOptions()
			chrome_options.add_argument('--proxy-server=http://%s' % PROXY)
			chrome = webdriver.Chrome(chrome_options=chrome_options)
			url = "http://" + uri
			pprint.pprint(url)
			chrome.get(url)
			time.sleep(3)
			chrome.quit()
			out = {"status":200,"message":"finished"}
			self.write(out)
			self.finish()


if __name__ == "__main__":
	application = tornado.web.Application([
        (r"/chromedriver", startHandler)
    ])

	application.listen(8555)

	tornado.ioloop.IOLoop.current().start()	