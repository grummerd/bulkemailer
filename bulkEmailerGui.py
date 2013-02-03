#!/usr/bin/env python

# bulkEmailerGui.py

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import threading
import email.header # used for debugging


from bulkEmailer import Bulk
from bulkEmailer import BulkDownloader
from bulkEmailer import Sender

 
class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)
 

class MainWindow:
    
    def delete_event(self, widget, event=None, data=None):
        self.abort = True
        gtk.main_quit()
        return False
    
    def run(self):
        self.abort = False
        self.run_thread = FuncThread(MainWindow.background_run, self)
        self.run_thread.start()
        
    def stop(self):
        self.abort = True
        self.stop_button.set_sensitive(False)
        
    def inform(self,msg):
        print msg
        gobject.idle_add(gtk.Label.set_text,self.stat_label,msg)
            
    def background_run(self):
        try:
            gobject.idle_add(gtk.Button.hide, self.go_button)
            gobject.idle_add(gtk.Button.set_sensitive, self.stop_button, True)
            gobject.idle_add(gtk.Button.show, self.stop_button)
        
            # download xml files of current user
            self.d = BulkDownloader('ftp://ftp.servage.net/',
                user='baruchhashem',pw='tribal12',target=u'inbox', crmUserId=26)
            gobject.idle_add(gtk.ProgressBar.pulse, self.progbar)

            for x in self.d.download_iter():
                if self.abort:
                    return
                self.inform(self.d.msg)
                gobject.idle_add(gtk.ProgressBar.pulse, self.progbar)

            self.inform(U'downloaded '+ str(self.d.downloaded))

            # send all files in the inbox
            bulk = Bulk(u'inbox')

            self.s = Sender(bulk)
            for x in self.s.send_iter():
                if self.abort:
                    return
                gobject.idle_add(gtk.ProgressBar.pulse, self.progbar)
                to_name, _, to_addr = self.s.msg['To'].partition(' ')
                self.inform(U'sent "' 
                    + email.header.decode_header(self.s.msg['Subject'])[0][0]
                    + U'" to ' 
                    + email.header.decode_header(to_name.strip('"'))[0][0] 
                    + U' ' + to_addr)
    
        except (EnvironmentError,ValueError) as e:
            self.inform(str(e))
        else:
            self.inform(U'Done')
        finally:
            gobject.idle_add(gtk.Button.hide, self.stop_button)
            gobject.idle_add(gtk.Button.show, self.go_button)
            gobject.idle_add(gtk.Button.set_sensitive, self.go_button, True)
            gobject.idle_add(gtk.ProgressBar.set_fraction, self.progbar, 0.0)

            
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(U"Bulk Emailer")
        self.window.connect("destroy", lambda wid: gtk.main_quit())
        self.window.connect("delete_event", self.delete_event)
        self.window.set_size_request(400,100)
        
        vbox = gtk.VBox(False,0)
        vbox.set_border_width(10)
        self.window.add(vbox)
        vbox.show()
        
        self.go_button = gtk.Button(label=U"Go")
        self.go_button.connect("clicked", lambda _: self.run())
        vbox.pack_start(self.go_button, False, False, 0)
        self.go_button.show()
        
        self.stop_button = gtk.Button(label=U"Stop")
        self.stop_button.connect("clicked", lambda _: self.stop())
        vbox.pack_start(self.stop_button, False, False, 0)
        self.stop_button.hide()
        
        self.progbar = gtk.ProgressBar()
        vbox.pack_start(self.progbar, False, False, 0)
        self.progbar.show()
        
        self.stat_label = gtk.Label()
        self.stat_label.set_line_wrap(False)
        self.stat_label.set_justify(gtk.JUSTIFY_LEFT)
        vbox.pack_start(self.stat_label, True, True, 0)
        self.stat_label.show()
        
        self.window.show()

        
if __name__ == "__main__":
    gobject.threads_init()
    main = MainWindow()
    gtk.main()
