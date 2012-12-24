#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Interact with config file in xml format.

import codecs
import xml.dom.minidom as DOM
from xml.dom.minidom import parseString
from egg import Egg

class ConfigXML(object):
	"""Interact with config file in xml format"""
	def __init__(self, strPackageName, strPath, strXMLFile):
		self.egg = Egg(strPackageName)
		self.config_full_path = self.egg.resource_filename(strPath, strXMLFile)
	
	def __del__(self):
		del self.config_full_path
		#Call class Egg's destructor
		del self.egg
	
	def save(self, dictData):
		"""	Save data to xml file in temp folder.
			Used to be called saveXMLData"""
		with codecs.open(self.config_full_path, "r", "utf-8", "replace") as fIn:
			strXML = fIn.read()
		dom = parseString(strXML)
		
		#Update xml values
		for strKey in dictData.keys():
			#Fix case: xml element (text node) "data" is non-existant ( i.e <pop3_port/> ) 
			child = dom.getElementsByTagName(strKey)[0].firstChild
			if child is None and dictData[strKey] is not None:
				parent = dom.getElementsByTagName(strKey)[0]
				child_text = dom.createTextNode('text')
				parent.appendChild(child_text)
				#createTextNode() then appendChild()
			else:
				pass
			
			try:
				dom.getElementsByTagName(strKey)[0].firstChild.data = dictData[strKey]
			except AttributeError, why:
				print "ConfigXML->save No key %(key)s" % {'key': strKey}
				print "\tdom", dom.getElementsByTagName(strKey)[0].firstChild
				pass
			else:
				#print "ConfigXML->save strKey %(key)s: %(value)s " % { 'key': strKey, 'value': dictData[strKey]}
				pass
		#Update temp file
		with codecs.open(self.config_full_path, "wb", "utf-8", "replace") as fOut:
			fOut.write( dom.toxml("utf-8") )
	
	def update(self, strKey, strValue):
		""" Replace a single key/value pair.
			Used to be called updateXMLDatum"""
		self.__init_dom()
		self.dom_config.getElementsByTagName(strKey)[0].firstChild.data = strValue
		#Update temp file
		with codecs.open(self.config_full_path, "wb", "utf-8", "replace") as fOut:
			fOut.write( self.dom_config.toxml("utf-8") )
		self.__del_dom()
	
	def __init_dom(self):
		"""	Set the xml dom into a class variable.
			Used to be called init_config_xml_dom.
			Called when using self.get OR self.update."""
		with codecs.open(self.config_full_path, "r", "utf-8", "replace") as fIn:
			strXML = fIn.read()
		self.dom_config = parseString(strXML)
		del strXML
		
	def __del_dom(self):
		del self.dom_config
	
	def get(self, strDataField="email_subject"):
		"""	Get the email subject from the xml config file.
			Used to be called configXMLData"""
		try:
			if self.dom_config:
				bolFound = True
		except AttributeError, why:
			bolFound = False
		else:
			bolFound = False
		
		if bolFound is not True:
			self.__init_dom()
		
		#Defensive coding: Handle situation specific xml tag not present in xml file.
		strXMLData = None
		try:
			strXMLData = self.dom_config.getElementsByTagName(strDataField)[0].firstChild.data
		except IndexError, why:
			pass
		except AttributeError, why:
			pass
		else:
			pass
		return strXMLData
