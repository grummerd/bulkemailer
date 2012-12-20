#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Interact with Python egg (zip) files. Python egg files will contain: 
icons image files, config files, templetes.
@Copyright Dave Landon Grummer 2012 <github@usguyintokyo.com>
"""

import pkg_resources, time, datetime, os, subprocess

class Egg(object):
  #Class to hold egg access methods
	def __init__(self, strPackageName):
		self.__package_name = strPackageName
	
	def __del__(self):
		"""We want to keep the config.xml file. So don't delete the contents of
		~/.python-eggs """
		#pkg_resources.cleanup_sources()
		pass
	
	def get_zipfile_path(self):
		#Get the zipfile location
		#[msgu 0.1a1 (/usr/local/lib/python2.7/dist-packages/msgu-0.1a1-py2.7.egg)]
		strEgg = False
		try:
			EggMetadata = pkg_resources.require(self.__package_name)
			strEgg = str(EggMetadata)
			del EggMetadata

			tupleEgg = strEgg.split("(")
			strEgg = tupleEgg[1]
			strEgg = strEgg[:len(strEgg)-2]
		except pkg_resources.DistributionNotFound as e:
			print "Python package %s not installed. So can't set the shipment date" % e.package_name
		else:
			pass
		return strEgg
	
	def resource_filename(self, strFallBackFolder, strResourcePath):
		#Try to get the resource from an egg. Fallback to getting from the file system
		strFileName = ""
		
		pathDefault = pkg_resources.get_default_cache()
		#Ensure that folder exists. If not make it
		if not os.path.exists(pathDefault):
			os.makedirs(pathDefault, 0744)
			#print "Created pathDefault %s" % pathDefault
		
		#Check if resource already has been extracted to temp folder.
		#Use the extracted resource if it exists.
		bolFound = False
		for (path, dirs, files) in os.walk(pathDefault):
			for name in files:
				if name == strResourcePath and bolFound != True:
					strFileName = os.path.join(path, name)
					bolFound = True
		
		#Extract resource (from egg)
		if bolFound != True:
			try:
				msgu = pkg_resources.Requirement.parse(self.__package_name)
				entries = pkg_resources.resource_listdir(msgu, strFallBackFolder)
				for entry in entries:
					#print "__egg_resource_filename resource entry %s" % entry
					if entry == strResourcePath:
						#resource found. Extract to pathDefault
						strFileName = pkg_resources.resource_filename(msgu, os.path.join(strFallBackFolder, entry) )
						bolFound = True
			except pkg_resources.ExtractionError:
				pass
			else:
				pass
		
		if not os.path.exists(strFileName):
			#get from file system
			#print "__egg_resource_filename (from file system) %s %s" % (strFallBackFolder, strResourcePath)
			strPackageDir = self.determine_path()
			strFileName = os.path.join (strPackageDir, strFallBackFolder, strResourcePath)
		return strFileName
	
	@staticmethod
	def enumFolder(strPackageName, strFolder):
		#Used by factory classes. So needs to be static.
		
		try:
			resourcePackage = pkg_resources.Requirement.parse(strPackageName)
			entries = pkg_resources.resource_listdir(resourcePackage, strFolder)
		except ImportError:
			entries = []
		return entries
	
	def copyOutFromZipFile(self, strFile, strDest):
		""" Copy file to destination form from egg file.
			This totally shouldn't work without root privledges, but does.
			So when in Rome."""
		strZipFile = self.get_zipfile_path()
		lngRetVal = False
		if strZipFile is not False:
			lngRetVal = subprocess.call(["unzip", "-ujo", strZipFile, strFile, "-d", strDest], shell=False, stdout=open(os.devnull, 'wb'))
		del strZipFile
		return lngRetVal
	
	def determine_path(self):
		#Determine the apps base folder
		root = __file__
		if os.path.islink (root):
			root = os.path.realpath (root)
		return os.path.dirname (os.path.abspath (root))
