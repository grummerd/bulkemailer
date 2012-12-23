#! /usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET # parse xml file with mail content
import os
import fnmatch # help locate xml files
import pickle # for persitence

from urlparse import urlparse
from ftplib import FTP # download bulk

# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

class Bulk:
    """An abstraction for the xml files with the mail content.
    """

    def __init__(self,location):
        """Prepare a list of valid xml files in the folder
        """
        self.xmlNames = []
        for file in os.listdir(location):
            if fnmatch.fnmatch(file, u'*.xml') \
            and ET.parse(file).getroot().tag == 'email_msg':
                self.xmlNames +=[file]
            
        # todo: improve sort (this one is buggy)
        self.xmlNames.sort()
        
        # immediately load first file
        self.oldXmlName = self.fName = self.xmlNames[0]
        self.root = ET.parse(self.fName)
        
    def recepients(self):
        """Iterable list of recepients.
        """
        for xmlName in self.xmlNames:
            if xmlName != self.fName:
                self.fName = xmlName
                self.root = ET.parse(self.fName)
            for email_to in self.root.findall(u'email_to'):
                yield email_to
                self.oldXmlName = self.fName
            #todo: erase file (maybe not here though)
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
                
    def _start(self):
        self.s = smtplib.SMTP(*bulk.smtp_server())
        self.s.login(*bulk.smtp_credentials())
        # Create a text/plain message
        self.msg = MIMEText(bulk.content())
        self.msg['Subject'] = bulk.subject()
        self.msg['From'] = u'"' + bulk.sender()['name'] + u'" ' \
            u'<' + bulk.sender()['addr'] + u'>'
    
    def _finish(self):
        if self.s:
            self.s.quit()
    
    def restart(self):
        self._finish()
        self._start()


    def run(self):
        try:
            self._start()
            for email_to in bulk.recepients():
                if self.bulk.changed():
                    self.restart()
                
                del self.msg['To']
                self.msg['To'] = '"' \
                    + email_to.find(u'name_encoded').text \
                    + u'" <' + email_to.attrib[u'addr'] + u'>'
                # send the mail
                self.s.sendmail(self.msg['From'], self.msg['To'], \
                    self.msg.as_string())
                print self.msg.as_string()
        
        finally:
            self._finish()

def download_bulk(url, user='anonymous', pw='',ext='.xml',target='.'):
    o = urlparse(url)
    if o.scheme != 'ftp':
        raise ValueError('only ftp supported')
    if o.path[-1:] != '/':
        raise ValueError('only directories supported')
    print 'conecting to',o.netloc
    ftp = FTP()
    try:
        ftp.connect(o.netloc)
        ftp.login(user,pw)
        ftp.cwd(o.path)
        os.chdir(target)
        for fname in ftp.nlst():
            if fname[-len(ext):] != ext:
                continue
            print 'downloading',fname
            f = open('./' + fname,'w')
            ftp.retrbinary('RETR ' + fname, \
                lambda chunk : f.write(chunk))
    finally:
        ftp.quit()
        


if __name__ == "__main__":
    # test download_bulk
    download_bulk('ftp://ftp.mozilla.org/pub/mozilla.org/firefox/releases/17.0/',\
        ext='.asc')
    bulk = Bulk(u'.')
    s = Sender(bulk)
    s.run()
