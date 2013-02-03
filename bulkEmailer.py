#! /usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET # parse xml file with mail content
import os
import fnmatch # help locate xml files
import pickle # for persitence
import time

from urlparse import urlparse
from ftplib import FTP # download bulk

# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
import email.header # used for debugging

from datetime import datetime # for sorting file names

import config_xml

# unit testing
import doctest

class Bulk:
    """An abstraction for the xml files with the mail content.
    """
    
    class XmlFname(str):
        """ Utility class for comparing xml file names.
        
        Used when sorting a list of such xml files
        """
 
        def __lt__(self,o):
            """ Compares two file names according to the date embedded
            in the file name
            
            returns True if the left one was created before the
            right one.
            e.g.
            >>> Bulk.XmlFname('2175_2012_12_13_05_52_59_de0c5040e94e41ade4a42d3738b598de.xml') < Bulk.XmlFname('2175_2012_12_12_05_52_59_de0c5040e94e41ade4a42d3738b587cd.xml')
            False
            >>> Bulk.XmlFname('2175_2012_12_12_05_52_59_de0c5040e94e41ade4a42d3738b587cd.xml') < Bulk.XmlFname('2175_2012_12_13_05_52_59_de0c5040e94e41ade4a42d3738b598de.xml')
            True
            """
            print self,o
            return \
                datetime.strptime(self[self.find('_'):self.rfind('_')], 
                    "_%Y_%m_%d_%H_%M_%S") \
                    < \
                datetime.strptime(o[o.find('_'):o.rfind('_')], 
                    "_%Y_%m_%d_%H_%M_%S")

    def __init__(self,location):
        """Prepare a list of valid xml files in the folder
        """
        self.loc = location
        self.xmlNames = []
        for file in os.listdir(self.loc):
            if fnmatch.fnmatch(file, u'*.xml') \
                and ET.parse(os.path.join(self.loc,file)) \
                .getroot().tag == 'email_msg':
                self.xmlNames +=[Bulk.XmlFname(file)]
        
        if len(self.xmlNames) == 0:
            raise ValueError(u"No files found")
        
        # sort by date (see XmlFname above)
        self.xmlNames.sort()
        
        # immediately load first file
        self.oldXmlName = self.fName = self.xmlNames[0]
        self.root = ET.parse(os.path.join(self.loc, self.fName))
        
    def recepients(self):
        """Iterable list of recepients.
        """
        for xmlName in self.xmlNames:
            if xmlName != self.fName:
                self.fName = xmlName
                self.root = ET.parse(os.path.join(self.loc, self.fName))
            for email_to in self.root.findall(u'email_to'):
                yield email_to
                self.oldXmlName = self.fName
            # assuming sending succeeded, erase XML file
            os.remove(os.path.join(self.loc, self.fName))
        # todo: consider persistence
    
    def content(self,mailtype='text'):
        """Content of the email, in text or html format.
        """
        if mailtype == 'text':
            return self.root.find('email_text').text
        elif mailtype == 'html':
            return self.root.find('email_html').text
        #else throw ?
        
    def smtp_server(self):
        return self.root.find("smtp_server").text, \
        self.root.find("smtp_port").text
    
    def smtp_credentials(self):
        return self.root.find("smtp_user").text, \
        self.root.find("smtp_pass").text
    
    def subject(self):
        return self.root.find('subject').text
    
    def sender(self):
        return {'addr' : self.root.find('from_addr').text, \
                'name' : self.root.find('from_name').text}
                
                
    def changed(self):
        """true if the file has changed between iteration steps
        """
        return self.oldXmlName != self.fName
        

class Sender:
    def __init__(self,bulk):
        self.bulk = bulk
        self.s = None
                
    def _start(self):
        try:
            self.s = smtplib.SMTP(*self.bulk.smtp_server())
            self.s.login(*self.bulk.smtp_credentials())
            # Create a text/plain message
            self.msg = MIMEText(self.bulk.content())
            self.msg['Subject'] = self.bulk.subject()
            self.msg['From'] = (u'"' + self.bulk.sender()['name'] + u'" ' +
                u'<' + self.bulk.sender()['addr'] + u'>')
            print (u'Preparing to send mail "' 
                + email.header.decode_header(self.msg['Subject'])[0][0] +'"...')
        except AttributeError:
            return
    
    def _finish(self):
        try:
            self.s.quit()
        except AttributeError as e:
            return
    
    def restart(self):
        self._finish()
        self._start()


    def send_iter(self):
        try:
            self._start()
            for email_to in self.bulk.recepients():
                if self.bulk.changed():
                    self.restart()
                
                del self.msg['To']
                self.msg['To'] = '"' \
                    + email_to.find(u'name_encoded').text \
                    + u'" <' + email_to.attrib[u'addr'] + u'>'
                # send the mail
                # todo: handle errors (esp. by retrying)
                # send mail
                self.s.sendmail(self.msg['From'], self.msg['To'], \
                    self.msg.as_string())
                yield
#        except Exception as e:
#            print e
        finally:
            self._finish()
    
    def run(self):
        for x in self.send_iter():
            print "sent to ", self.msg['To']

class BulkDownloader:
    def __init__(self, url, user='anonymous', pw='', \
        ext='.xml',target='.', crmUserId = 26):
        self.crmUserId = crmUserId
        self.o = urlparse(url)
        if self.o.scheme != 'ftp':
            raise ValueError('only ftp supported')
        if self.o.path[-1:] != '/':
            raise ValueError('only directories supported')
        self.user = user
        self.pw = pw
        self.ext = ext
        self.downloaded = [] # list of downloaded files
        
        # create target path if it doesn't exist
        if not os.access(target,os.F_OK):
            os.makedirs(target)
        self.target = target

    def download(self):
        for x in self.download_iter():
            print self.msg

    # break downloading into smaller steps, to allow a more flexible UI
    def download_iter(self):
        ftp = FTP()
        try:
            self.msg = 'conecting to ' + self.o.netloc
            ftp.connect(self.o.netloc)
            yield
            self.msg =  'logging in as ' + self.user
            ftp.login(self.user,self.pw)
            yield
            self.msg = 'accessing ' + self.o.path
            ftp.cwd(self.o.path)
            yield
            for fname in ftp.nlst():
                if fname[-len(self.ext):] != self.ext:
                    continue #only download .xml files
                if int(fname[0:fname.find('_')]) != self.crmUserId:
                    continue # only download files created by this user
                
                with open(os.path.join(self.target,fname),'w') as f:
                    ftp.retrbinary('RETR ' + fname, lambda c : f.write(c))
                self.downloaded += [fname]
                self.msg = 'downloaded ' + fname
                yield
        finally:
            print "ftp disconnected"
            ftp.quit()
           
        print 'downloaded',self.downloaded
     


if __name__ == "__main__":
    doctest.testmod() # unit testing 
    
    # download xml files of current user
    d = BulkDownloader('ftp://ftp.servage.net/', \
        user='baruchhashem',pw='tribal12',target=u'inbox', crmUserId=26)
    d.download()
    
    # send all files in the inbox
    bulk = Bulk(u'inbox')
    s = Sender(bulk)
    s.run()

