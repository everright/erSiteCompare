#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Compare two sites for given URLs.
Use selenium Firefox webdirver to capture screenshots of site pages.
It will be generate compare reports with friendly html format.

Author: everright.chen
Email: everright.chen@gmail.com
Website: http://everright.cn
Github: https://github.com/everright
Version: 1.0 Beta
"""

import os, sys, time, urllib, logging, errno, json, zipfile, shutil
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from hashlib import md5
from PIL import Image, ImageChops
import math, operator
import optparse

PY3k = sys.version_info >= (3,)
if PY3k:
    from urllib.parse import urlencode
    from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl
else:
    from urllib import urlencode
    from urlparse import urljoin, urlparse, urlunparse, parse_qsl

class Url(object):
    def __init__(self, url):
        self.scheme, self.netloc, self.path, self.params, self.query_string, self.fragment = urlparse(url)
        self.query = dict(parse_qsl(self.query_string))

    def build(self):
        return u"%s" % urlunparse((self.scheme, self.netloc, self.path, self.params, urlencode(self.query), self.fragment))

    def __str__(self):
        return self.build()

    def __unicode__(self):
        return self.build()

class imageCompare(object):
	_pointTable = ([0] + ([255] * 255))
	_image1 = None
	_image2 = None
	_rms = None

	def __init__(self, image1 = None, image2 = None):
		if not os.path.exists(image1):
			sys.exit('Image1 file [%s] does not exist.' % image1)
		if not os.path.exists(image2):
			sys.exit('Image2 file [%s] does not exist.' % image2)

		self._image1 = Image.open(image1)
		self._image2 = Image.open(image2)
		print 'Compare image1 [%s] with image2 [%s].' % (image1, image2)

	def __del__(self):
		self._image1 = None
		self._image2 = None

	def image_similarity(self):
		h1 = self._image1.histogram()
		h2 = self._image2.histogram()
		self._rms = math.sqrt(reduce(operator.add, map(lambda a, b: (a - b) ** 2, h1, h2)) / len(h1))
		return self._rms

	def image_similarity_image(self):
		diff = ImageChops.difference(self._image1, self._image2)
		diff = diff.convert('L')
		diff = diff.point(self._pointTable)
		image = diff.convert('RGB')
		image.paste(self._image2, mask=diff)
		return image

	def image_save(self, target):
		if (0.0 == self._rms):
			return False
		dirname = os.path.dirname(target)
		self.mkdir(dirname)
		image = self.image_similarity_image()
		image.save(target)
		return True

	def mkdir(self, path):
		if ('' == path or os.path.isdir(path)):
			return
		try:
			os.makedirs(path)
		except OSError, e:
			if (e.errno != errno.EEXIST):
				raise e

class siteCompare(object):
	_scrapeQueue = []
	_siteLinks = {}
	_windowOpenLinks = []
	_siteLinkCaptures = {}
	_site1Links = {}
	_site2Links = {}
	_compareImages = {}
	_compareResult = []
	_resultCount = 1
	_logFile = 'webcompare.log'
	_template = None
	_outputPath = None
	_site1 = None
	_site2 = None
	_site1Capture = 'site1'
	_site2Capture = 'site2'
	_siteCapture = 'site'
	_capturePath = None
	_baseDomain = None
	driver = None

	def __init__(self, site1 = None, site2 = None, output = None, template = None, logLevel = logging.DEBUG, profile = None):
		if output:
			self._outputPath = output
			self.mkdir(output)

		if template:
			self._template = template

		logging.basicConfig(filename = os.path.join(self._outputPath, self._logFile), level = logLevel, format = '%(asctime)s - %(levelname)s: %(message)s')

		if (len(site1) < 10 or 'http' not in site1):
			logging.error('Inavlid site1 url [%s].' % site1)
			sys.exit('Inavlid site1 url [%s].' % site1)
		if (len(site2) < 10 or 'http' not in site2):
			logging.error('Inavlid site2 url [%s].' % site2)
			sys.exit('Inavlid site2 url [%s].' % site2)
		if (site1 == site2):
			logging.error('Sites compare should be use different url, site1 [%s], site2 [%s].' % (site1, site2))
			sys.exit('Sites compare should be use different url.')

		conn = urllib.urlopen(site1)
		if (200 != conn.getcode()):
			logging.error('System connect to site1 [%s] failed.' % site1)
			sys.exit('System connect to site1 [%s] failed, please check the network.' % site1)

		conn = urllib.urlopen(site2)
		if (200 != conn.getcode()):
			logging.error('System connect to site2 [%s] failed.' % site2)
			sys.exit('System connect to site2 [%s] failed, please check the network.' % site2)

		self._site1 = site1
		self._site2 = site2

		try:
			if profile is not None:
				fp = webdriver.FirefoxProfile(profile)
				self.driver = webdriver.Firefox(fp)
			else:
				self.driver = webdriver.Firefox()
			self.driver.implicitly_wait(30)
			self.driver.maximize_window()
		except WebDriverException, e:
			raise e

		logging.info('Sites compare start.')

	def __del__(self):
		if (self.driver):
			self.driver.quit()
			logging.info('Sites compare end.')

	def clear(self):
		self._scrapeQueue = []
		self._siteLinks = {}
		self._windowOpenLinks = []

	def baseDomain(self, url):
		urls = Url(url)
		self._baseDomain = urls.netloc

	def sameDomain(self, url):
		urls = Url(url)
		return (self._baseDomain == urls.netloc)

	def removeDomain(self, url):
		urls = Url(url)
		urls.scheme = ''
		urls.netloc = ''
		newurl = urls.build()
		if '' == newurl:
			newurl = '/'
		return newurl

	def saveFile(self, data, target):
		dirname = os.path.dirname(target)
		self.mkdir(dirname)
		f = open(target, 'w')
		f.write(data)
		f.flush()
		f.close()

	def saveSite1CaptureResult(self):
		for key, value in self._siteLinks.items():
			key = self.removeDomain(key)
			self._site1Links[key] = value
		self._site1LinkCaptures = self._siteLinkCaptures
		fp = os.path.join(self._capturePath, self._site1Capture + '.json')
		data = json.dumps(self._site1Links)
		self.saveFile(data, fp)
		self.clear()

	def saveSite2CaptureResult(self):
		for key, value in self._siteLinks.items():
			key = self.removeDomain(key)
			self._site2Links[key] = value
		self._site2LinkCaptures = self._siteLinkCaptures
		fp = os.path.join(self._capturePath, self._site2Capture + '.json')
		data = json.dumps(self._site2Links)
		self.saveFile(data, fp)
		self.clear()

	def saveCompareResult(self):
		fp = os.path.join(self._outputPath, 'result.json')
		data = {"page":1,"total":1,"records":len(self._compareResult),"rows":self._compareResult}
		data = json.dumps(data)
		self.saveFile(data, fp)

	def startSite1(self):
		self.baseDomain(self._site1)
		self._capturePath = os.path.join(self._outputPath, self._site1Capture)
		print 'Site1 [%s] start, capture save path: %s' % (self._site1, self._capturePath)
		self.mkdir(self._capturePath)
		self.appendLinks(self._site1)
		self.scrape()
		self.saveSite1CaptureResult()

	def startSite2(self):
		self.baseDomain(self._site2)
		self._capturePath = os.path.join(self._outputPath, self._site2Capture)
		print 'Site2 [%s] start, capture save path: %s' % (self._site2, self._capturePath)
		self.mkdir(self._capturePath)
		self.appendLinks(self._site2)
		self.scrape()
		self.saveSite2CaptureResult()

	def mkdir(self, path):
		if ('' == path or os.path.isdir(path)):
			return
		try:
			os.makedirs(path)
		except OSError, e:
			if (e.errno != errno.EEXIST):
				raise e

	def appendLinks(self, link):
		url = Url(link)
		if (self._baseDomain == url.netloc):
			url.fragment = ''
			link = url.build()
			if not self._siteLinks.has_key(link):
				self._siteLinks[link] = ''
				self._scrapeQueue.append(link)
				logging.info('Append new link [%s].' % link)

	def prepareLinks(self, tagName):
		key = 'href'
		if ('frame' == tagName or 'iframe' == tagName):
			key = 'src'
		elements = self.driver.find_elements_by_tag_name(tagName)
		if elements:
			for el in elements:
				link = el.get_attribute(key)
				if not link:
					continue
				logging.info('Find link [%s].', link)
				link = link.lower()
				if (str(link)[0:4] == 'http'):
					self.appendLinks(link)

	def getLinks(self, url):
		print "Processing %s" % (url)
		self.driver.get(url)
		self.prepareLinks('a')
		#self.prepareLinks('area')
		#self.prepareLinks('frame')
		#self.prepareLinks('iframe')

	def windowOpen(self):
		elements = self.driver.find_elements_by_xpath("//a[contains(@href,'window.open')]")
		if elements:
			for el in elements:
				link = el.get_attribute('href')
				if not link:
					continue
				link = link.lower()
				if (link in self._windowOpenLinks):
					continue
				el.click()
				aw = self.driver.window_handles
				self.driver.switch_to_window(aw[1])
				fn = self.saveCapture()
				self._windowOpenLinks.append(link)
				self._siteLinks[self.driver.current_url] = fn
				self.driver.close()
				self.driver.switch_to_window(aw[0])

 	def saveCapture(self):
		url = self.driver.current_url
		newurl = self.removeDomain(url)
		m = md5(newurl)
		fn = m.hexdigest() + '.png'
		fp = os.path.join(self._capturePath, fn)
		logging.info('Save capture [%s] of link [%s].' %(url, fp))
		self._siteLinkCaptures[fn] = newurl
		self.driver.save_screenshot(fp)
		return fn

	def scrape(self):
		while self._scrapeQueue:
			url = self._scrapeQueue.pop(0)
			self.getLinks(url)
			self.windowOpen()
			fn = self.saveCapture()
			self._siteLinks[url] = fn

	def capture(self):
		self.startSite1()
		self.startSite2()

	def compareImage(self, filename):
		if self._compareImages.has_key(filename):
			return self._compareImages[filename]
		fn1 = os.path.join(self._site1Capture, filename)
		f1 = os.path.join(self._outputPath, fn1)
		fn2 = os.path.join(self._site2Capture, filename)
		f2 = os.path.join(self._outputPath, fn2)
		c = imageCompare(image1 = f1, image2 = f2)
		disparity = c.image_similarity()
		fn = os.path.join(self._siteCapture, filename)
		fp = os.path.join(self._outputPath, fn)
		view = ''
		if c.image_save(fp):
			view = '<a href="%s" rel="shadowbox[images]" title="%s">view</a>' % (fn, fn)

		onlieCompare = '<a href="#" class="compare" image1="%s" image2="%s">compare</a>' % (fn1, fn2)
		self._compareImages[filename] = (disparity, view, onlieCompare)
		return self._compareImages[filename]

	def buildSiteLink(self, link, web = 'site1'):
		if '' == link:
			return link

		url = ''
		if 'site1' == web:
			url = self._site1.rstrip('/') + link
		else:
			url = self._site2.rstrip('/') + link

		output = '<a href="%s" rel="shadowbox" title="%s">%s</a>' % (url, link, link)
		return output	

	def compareResult(self, site1Link, site1Target, site2Link, site2Target, filename):
		site1Link = self.buildSiteLink(site1Link)
		site1Target = self.buildSiteLink(site1Target)
		site2Link = self.buildSiteLink(site2Link)
		site2Target = self.buildSiteLink(site2Target)
		disparity = ''
		view = ''
		onlieCompare = ''
		if site1Link == site2Link:
			disparity, view, onlieCompare = self.compareImage(filename)
		result = (self._resultCount, site1Link, site1Target, site2Link, site2Target, disparity, view, onlieCompare)
		data = {'id':self._resultCount,'cell':result}
		self._resultCount += 1
		self._compareResult.append(data)

	def compare(self):
		if (self._site1Links):
			for link, filename in self._site1Links.items():
				site1Link = link
				site1Target = self._siteLinkCaptures[filename]
				site2Link = ''
				site2Target = ''
				if self._site2Links.has_key(link):
					del self._site2Links[link]
					site2Link = site1Link
					site2Target = site1Target
				self.compareResult(site1Link, site1Target, site2Link, site2Target, filename)

		if (self._site2Links):
			for link, filename in self._site2Links.items():
				site1Link = ''
				site1Target = ''
				site2Link = link
				site2Target = self._siteLinkCaptures[filename]
				self.compareResult(site1Link, site1Target, site2Link, site2Target, filename)

		self.saveCompareResult()

	def download(self, url, filename):
		print 'Download file %s' % url
		f = open(filename, 'w')
		f.write(urllib.urlopen(url).read())
		f.close()

	def reportTemplate(self):
		templateFile = None
		if os.path.isfile(self._template) and os.path.exists(self._template):
			templateFile = self._template
		else:
			templateFile = os.path.join(self._outputPath, 'template.zip')
			self.download(self._template, templateFile)
		zf = zipfile.ZipFile(templateFile)
		zf.extractall(self._outputPath)
		zf.close()
		tempPath = os.path.join(self._outputPath, 'erSiteCompare-template')
		if os.path.isdir(tempPath) and os.path.exists(tempPath):
			shutil.move(os.path.join(tempPath, 'index.html'), os.path.join(self._outputPath, 'index.html'))
			shutil.move(os.path.join(tempPath, 'js'), os.path.join(self._outputPath, 'js'))
			shutil.move(os.path.join(tempPath, 'css'), os.path.join(self._outputPath, 'css'))
			shutil.rmtree(tempPath)

	def run(self):
		self.capture()
		self.compare()
		self.reportTemplate()

def main(args=None):
	_template = 'https://github.com/everright/erSiteCompare/archive/template.zip'
	usage = "Usage: %prog [options] URL1 URL2"
	parser = optparse.OptionParser(usage=usage, version="%prog 1.0 Beta")
	parser.add_option('-d', '--debug', action='store_true', dest='debug',
		help='show debug messages during sites compare')
	parser.add_option('-o', '--output', metavar="PATH", action='store', dest='output',
		help='save site screenshots and results of sites compare')
	parser.add_option('-p', '--profile', metavar="PROFILE", action='store', dest='profile',
		help='start firefox with special profile')
	parser.add_option('-t', '--template', metavar="URL", action='store', dest='template',
		help='compare report html template file or download url, default is: %s' % _template)
	options, args = parser.parse_args()

    # TODO:
	if len(args) != 2:  
		parser.error('Incorrect number of arguments')

	_site1 = args[0]
	_site2 = args[1]

	_level = logging.INFO
	if options.debug:
		_level = logging.DEBUG

	_output = 'result'
	if options.output:
		_output = options.output

	_profile = None
	if options.profile:
		if os.path.exists(options.profile):
			_profile = options.profile
		else:
			parser.error('Firefox special profile [%s] does not exist.' % options.profile)

	if options.template:
		_template = options.template

	# START
	sites = siteCompare(site1 = _site1, site2 = _site2, output = _output, template = _template, logLevel = _level, profile = _profile)
	sites.run()

if __name__ == '__main__':
	sys.exit(main())
