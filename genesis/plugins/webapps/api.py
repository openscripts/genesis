from genesis.com import *
from genesis import apis

import ConfigParser
import glob
import os
import re


class Webapps(apis.API):
	def __init__(self, app):
		self.app = app

	class IWebapp(Interface):
		name = ''
		dpath = ''
		icon = 'gen-earth'
		php = False
		nomulti = False
		addtoblock = ''
		ssl = False

		def pre_install(self, name, vars):
			pass

		def post_install(self, name, path, vars):
			pass

		def pre_remove(self, name, path):
			pass

		def post_remove(self, name):
			pass

		def get_info(self):
			pass

		def ssl_enable(self, path, cfile, kfile):
			pass

		def ssl_disable(self, path):
			pass

	def get_apptypes(self):
		applist = []
		for plugin in self.app.grab_plugins(apis.webapps.IWebapp):
			applist.append(plugin)
		return applist

	def get_sites(self):
		applist = []
		if not os.path.exists('/etc/nginx/sites-available'):
			os.makedirs('/etc/nginx/sites-available')
		if not os.path.exists('/etc/nginx/sites-enabled'):
			os.makedirs('/etc/nginx/sites-enabled')

		for site in os.listdir('/etc/nginx/sites-available'):
			# Set default values and regexs to use
			addr = False
			port = '80'
			php = False
			stype = 'Unknown'
			path = os.path.join('/etc/nginx/sites-available', site)
			rtype = re.compile('.*?# GENESIS ((?:[a-z][a-z]+))', flags=re.IGNORECASE)
			rport = re.compile('.*?listen (\\d+)\s*(.*?);')
			raddr = re.compile('.*?server_name ([^\s]+).*?;', flags=re.IGNORECASE)
			rpath = re.compile('.*?root ((?:\\/[\\w\\.\\-]+)+).*?;', flags=re.IGNORECASE)
			rphp = re.compile('.*?index .*?php.*?;', flags=re.IGNORECASE)

			# Get actual values
			f = open(os.path.join('/etc/nginx/sites-available', site), 'r')
			for line in f.readlines():
				if re.match(rtype, line):
					stype = re.match(rtype, line).group(1)
				elif re.match(rport, line):
					port = re.match(rport, line).group(1)
					ssl = re.match(rport, line).group(2)
				elif re.match(raddr, line):
					addr = re.match(raddr, line).group(1)
				elif re.match(rpath, line):
					path = re.match(rpath, line).group(1)
				elif re.match(rphp, line):
					php = True
			if os.path.exists(os.path.join('/etc/nginx/sites-enabled', site)):
				enabled = True
			else:
				enabled = False

			cls = self.get_interface(stype)
			if hasattr(cls, 'ssl'):
				ssl_able = cls.ssl
			else:
				ssl_able = False

			# Create dict of values
			applist.append({
					'name': site,
					'type': stype,
					'ssl': (True if ssl == 'ssl' else False),
					'ssl_able': ssl_able,
					'addr': addr, 
					'port': port,
					'path': path, 
					'php': php,
					'class': cls,
					'enabled': enabled
				})
			f.close()
		return applist

	def get_interface(self, name):
		interface = ''
		for plugin in self.app.grab_plugins(apis.webapps.IWebapp):
			if plugin.__class__.__name__ == name:
				interface = plugin
		return interface

	def cert_remove_notify(self, name, stype):
		# Called by webapp when removed.
		# Removes the associated entry from gcinfo tracker file
		# Placed here for now to avoid awkward circular import
		try:
			cfg = ConfigParser.ConfigParser()
			for x in glob.glob('/etc/ssl/certs/genesis/*.gcinfo'):
				cfg.read(x)
				alist = []
				write = False
				for i in cfg.get('cert', 'assign').split('\n'):
					if i != (name+' ('+stype+')'):
						alist.append(i)
					else:
						write = True
				if write == True:
					cfg.set('cert', 'assign', '\n'.join(alist))
					cfg.write(open(x, 'w'))
		except:
			pass
