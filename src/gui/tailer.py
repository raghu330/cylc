#!/usr/bin/env python

import gobject
import threading
import os, re
import tail

class tailer(threading.Thread):
    def __init__( self, logview, log, proc=None, tag=None, warning_re=None, critical_re=None ):
        super( tailer, self).__init__()
        self.logview = logview
        self.logbuffer = logview.get_buffer()
        self.logfile = log
        self.quit = False
        self.tag = tag
        self.proc = proc
        self.freeze = False
        self.warning_re = warning_re
        self.critical_re = critical_re
        self.warning_tag = self.logbuffer.create_tag( None, foreground = "orangered" )
        self.critical_tag = self.logbuffer.create_tag( None, foreground = "magenta" )
 
    def clear( self ):
        s,e = self.logbuffer.get_bounds()
        self.logbuffer.delete( s,e )

    def run( self ):
        #gobject.idle_add( self.clear )
        #print "Starting tailer thread"

        if not os.path.exists( self.logfile ):
            #gobject.idle_add( self.warn, "File not found: " + self.logfile )
            print "File not found: " + self.logfile
            #print "Disconnecting from tailer thread"
            return

        gen = tail.tail( open( self.logfile ))
        while not self.quit:
            if not self.freeze:
                line = gen.next()
                if line:
                    gobject.idle_add( self.update_gui, line )
            if self.proc != None:
                # poll the subprocess; this reaps its exit code and thus
                # prevents the pid of the finished process staying in
                # the OS process table (a "defunct process") until the
                # parent process exits.
                self.proc.poll()
            # The following doesn't work, not sure why, perhaps because
            # the top level subprocess finishes before the next one
            # (shows terminated too soon). 
            #    if self.proc.poll() != None:
            #        (poll() returns None if process hasn't finished yet.)
            #        #print 'process terminated'
            #        gobject.idle_add( self.update_gui, '(PROCESS COMPLETED)\n' )
            #        break
        #print "Disconnecting from tailer thread"
 
    def update_gui( self, line ):
        if self.critical_re and re.search( self.critical_re, line ):
            self.logbuffer.insert_with_tags( self.logbuffer.get_end_iter(), line, self.critical_tag )
        elif self.warning_re and re.search( self.warning_re, line ):
            self.logbuffer.insert_with_tags( self.logbuffer.get_end_iter(), line, self.warning_tag )
        elif self.tag:
            self.logbuffer.insert_with_tags( self.logbuffer.get_end_iter(), line, self.tag )
        else:
            self.logbuffer.insert( self.logbuffer.get_end_iter(), line )
        self.logview.scroll_to_iter( self.logbuffer.get_end_iter(), 0 )
        return False
