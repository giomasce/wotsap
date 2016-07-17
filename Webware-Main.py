#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# This file is meant to be used with Webware (http://webware.sf.net/).
# Part of Web of trust statistics and pathfinder, Wotsap
# Copyright (C) 2003  Jörgen Cederlöf <jc@lysator.liu.se>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

dumpfile   = "/web/users/roxen_only/jc/wotsap/wots/latest.wot"

url = "http://webware.lysator.liu.se/jc/"

minsize     = 200,50
maxsize     = 2000,2000
defaultsize = 980,700

maxwanted = 1000

from WebKit.Page import Page
import sys
import os
import wotsap
import re

# _foo=[bar] arguments is an idiom for static variables.
# An argument gets its default value only once, so if it is mutable it
# can be changed. The underscore is there to remind the caller that
# the variable is internal.
# TODO This should be called once in a while by some sort of timer, to
# avoid long load times for the first request. Is that possible with
# Webware?
def getlatestwot(path=dumpfile, _lastmtime=[0], _wot=[None]):
    if os.lstat(path).st_mtime != _lastmtime[0]:
        _lastmtime[0]   = os.lstat(path).st_mtime
        wot = wotsap.Wot(path)
        wot.initfont()
        _wot[0]  = wot
    return _wot[0]

def handlelegacyurl(wot, fields, redirect):
    """Handle the early, now obsolete, URL scheme."""
    def fieldtokey(field, regexp="^0x[0-9a-fA-F]{8}$"):
        if field in fields and  re.compile(regexp).search(fields[field]):
            return fields[field]
    bottom, top = fieldtokey('bottom'), fieldtokey('top')
    if bottom and top:
        size = fieldtokey('size', '^[0-9]+x[0-9]+$')
        if size: args = "?size=" + size
        else:    args = ""
        redirect(url+"wotsap/wots/latest/paths/%s-%s.png%s"%(bottom,top,args))
    elif top:
        redirect(url+"wotsap/wots/latest/keystatistics/%s.txt"%top)
    else:
        redirect("http://www.lysator.liu.se/~jc/wotsap/")

def handleurl(urlpath, fields, write, setheader, redirect, urlencode):
    """Parse URL and take appropriate action."""
    wot = getlatestwot()
    # Arguments
    def checkfields(allowedfields, mandatoryfields=()):
        ret = ""
        for field in fields:
            if field not in mandatoryfields:
                if field not in allowedfields:
                    raise ValueError('Unknown field "%s".' % field)
                if fields[field]:
                    if not ret: ret += '?'
                    else:       ret += '&'
                    ret += '%s=%s' % (urlencode(field),
                                      urlencode(fields[field]))
        for field in mandatoryfields:
            if field not in fields or not fields[field]:
                raise ValueError('Mandatory field "%s" not specified.' % field)
        return ret
    modstring = fields.get('modstring', None)
    if 'size' in fields and fields['size']:
        try:
            size = fields['size'].split('x', 1)
            size = int(size[0]), int(size[1])
            if not minsize[0] <= size[0] <= maxsize[0] or \
               not minsize[1] <= size[1] <= maxsize[1]:
                raise ValueError(
                    'Size too large or too small: %s\n'%fields['size'] +\
                    'It must be between %dx%d and %dx%d, inclusive.\n' % (minsize+maxsize))
        except IndexError, err:
            raise ValueError('Error in size "%s". Size must be in format ' \
                             '"1024x768".' % fields['size'])
    else:
        size = defaultsize
    if 'date' in fields and fields['date']:
        raise NotImplementedError('Error: date not implemented yet.')
    # Parse URLpath
    kre = "0x[0-9a-fA-F]{8}"
    def matches(regexp):
        return re.compile(regexp).search(urlpath)
    # Remove double slashes
    tmp = -1
    while tmp != len(urlpath):
        tmp = len(urlpath)
        urlpath = urlpath.replace('//', '/')
    del tmp
    if urlpath[0:1] == "/":
        urlpath = urlpath[1:]
    # Empty URLpath?
    if   matches("^/*$"):
        redirect("http://www.lysator.liu.se/~jc/")
        return
    # Legacy URLpath?
    elif matches("^wotsap/$"):
        if not fields: # We dont support statistics this way anymore.
            redirect("http://www.lysator.liu.se/~jc/wotsap/")
        else:
            return handlelegacyurl(wot, fields, redirect)
    # Action.
    elif matches('^wotsap/wots/latest/wotinfo.txt$'):
        checkfields([])
        setheader('Content-type', 'text/plain; charset=utf-8' )
        write(wot.wotstats().encode('utf-8', 'replace'))
    elif matches('^wotsap/wots/latest/debuginfo.txt$'):
        checkfields([])
        setheader('Content-type', 'text/plain; charset=utf-8' )
        write(wot.debug.encode('utf-8', 'replace'))
    elif matches('^wotsap/wots/latest/keystatistics/%s\\.txt$'%kre):
        args = checkfields(['modstring', 'wanted', 'restrict'])
        wanted   = fields.get('wanted',   0)
        restrict = fields.get('restrict', None)
        if wanted:
            wanted = int(wanted)
            if wanted > maxwanted:
                raise ValueError(
                    'Too large wanted value %d. It must be no larger than %d.'\
                    % (wanted, maxwanted))
        key = urlpath[-14:-4]
        timer = {'time'     : 8,
                 'fraction' : 0.10,
                 'action'   : 'raise'}
        try:
            stats = wot.keystats(key, modstring=modstring, wanted=wanted,
                                 restrict=restrict, timer=timer).encode('utf-8', 'replace')
        except wotsap.wotTimeoutError, err:
            setheader('Content-type', 'text/plain; charset=utf-8' )
            err.times['appendstring'] = \
                     '\nSorry, this is to much. Try restricting to fewer keys or run the stand-alone program.\n'\
                     'Or look at http://keyserver.kjsl.com/~jharris/ka/current/top50table.html.\n'
            raise ValueError(str(err))
        setheader('Content-type', 'text/plain; charset=utf-8' )
        write(stats)
    elif matches('^wotsap/wots/latest/paths/%s-%s\\.png$'%(kre,kre)):
        checkfields(['modstring', 'size'])
        bottomkey = urlpath[-25:-15]
        topkey    = urlpath[-14: -4]
        web   = wot.findpaths(bottomkey, topkey, modstr=modstring)
        graph = wot.creategraph(web, config={'size': size}, format="PIL")
        setheader('Content-type', 'image/png')
        tmpwrite = write
        class tmpfile:
            # PIL documentation says we need seek, tell, and write,
            # but write seems to be sufficient.
            write = tmpwrite
        graph.save(tmpfile, 'png')
    elif matches('^wotsap/wots/latest/groupmatrix/%s(,%s)*\\.txt$'%(kre,kre)):
        checkfields(['modstring'])
        keys = urlpath[31:-4]
        setheader('Content-type', 'text/plain; charset=utf-8')
        for line in wot.groupmatrix(keys, modstring=modstring):
            write(line.encode('utf-8', 'replace') + '\n')
    # Searches
    # raise wot.wotKeyNotFoundError(str2key(path[14:24]))
    elif matches('^wotsap/search/wotinfo$'):
        checkfields([])
        redirect(url+"wotsap/wots/latest/wotinfo.txt")
    elif matches('^wotsap/search/debuginfo$'):
        checkfields([])
        redirect(url+"wotsap/wots/latest/debuginfo.txt")
    elif matches('^wotsap/search/keystatistics$'):
        args = checkfields(['modstring', 'wanted', 'restrict'], ['key'])
        key = wot.nametokey(fields['key'])
        redirect(url+"wotsap/wots/latest/keystatistics/%s.txt"%key +args)
    elif matches('^wotsap/search/paths$'):
        args = checkfields(['modstring', 'size'], ['bottom', 'top'])
        bottom = wot.nametokey(fields['bottom'])
        top    = wot.nametokey(fields['top'   ])
        redirect(url+"wotsap/wots/latest/paths/%s-%s.png"%(bottom,top) +args)
    elif matches('^wotsap/search/groupmatrix$'):
        args = checkfields(['modstring'], ['keys'])
        namelist = fields['keys'].split(',')
        if len(namelist) > 1:
            keys = ','.join([wot.nametokey(name) for name in namelist])
            redirect(url+"wotsap/wots/latest/groupmatrix/%s.txt"%keys +args)
        else:
            setheader('Content-type', 'text/plain; charset=utf-8')
            for line in wot.groupmatrix(None, searchstring=namelist[0],
                                        modstring=modstring):
                write(line.encode('utf-8', 'replace') + '\n')
    elif matches('^wotsap/search/listkeys$'):
        args = checkfields([], ['keys'])
        setheader('Content-type', 'text/plain; charset=utf-8')
        for name in wot.listkeys(fields['keys']):
            write(name.encode('utf-8', 'replace') + '\n')
    else: # Unknown URLpath
        redirect("http://www.lysator.liu.se/~jc/wotsap/")
        #setheader('Content-type', 'text/plain; charset=utf-8')
        #write("Unknown path: ")
        #write(urlpath.encode('utf-8', 'replace') + '\n')
        #write(str(fields) + '\n')

def errorwrapper(urlpath, fields, write, setheader, sendredirect, urlencode):
    try:
        return handleurl(urlpath, fields, write, setheader, sendredirect, urlencode)
    except (ValueError, NotImplementedError, wotsap.wotTooManyError,
            wotsap.wotKeyNotFoundError, wotsap.wotModstringError), err:
        setheader('Content-type', 'text/plain; charset=utf-8')
        write(unicode(err).encode('utf-8', 'replace'))

# Every time someone requests a page, Webware calls Main.writeHTML. 
# Webware is kind enough to give us both the whole URL between
# "http://webware.lysator.liu.se/jc/" and "?", and both GET and POST
# form entries nicely interpreted and put into a dictionary. All we
# have to do is parse these and take appropriate action.
class Main(Page):
    def writeHTML(self):
        request  = self.request()
        sendredirect = self.response().sendRedirect
        setheader    = self.response().setHeader
        urlencode    = self.urlEncode
        fields       = self.request().fields()
        urlpath      = self.request().originalURLPath() 
        write        = self.write

        # Useful when debugging:
        #def sendredirect(url):
        #    setheader('Content-type', 'text/plain; charset=utf-8')
        #    write('Intercepted redirect to: %s' % url)
        
        # The strings we get from Webware are just the 7bit URL
        # decoded to 8bit octet streams. HTML4.01 says that that
        # stream is latin1 encoded. In practice, things are very
        # complicated. See e.g.
        # http://ppewww.ph.gla.ac.uk/~flavell/charset/form-i18n.html
        # . It seems to indicate that browsers often choose the same
        # encoding as the web page the form is on. If we code the web
        # page in iso-8859-1, both that rule and the HTML4.01 spec
        # says that the string should be iso-8859-1. This will make it
        # impossible to enter other characters. The only other simple
        # alternative would be to have the web page coded in UTF-8 and
        # treat all form data as UTF-8, but that would mean that
        # standards-conforming browsers wouldn't be able to send
        # non-ASCII iso-8859-1 characters. Tons of other heuristics
        # exists if someone wants to make it more stable.
        urlpath = urlpath.decode('iso-8859-1', 'replace')
        for key in fields: # The field names themselves are ascii.
            fields[key] = fields[key].decode('iso-8859-1', 'replace')
        return errorwrapper(urlpath, fields, write, setheader, sendredirect, urlencode)
