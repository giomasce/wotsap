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

dumpfile   = "/web/Webwaredirs/jc/db/dump.wot"
debiandump = "/web/Webwaredirs/jc/db/dump-debian.wot"
fontfile   = "/web/Webwaredirs/jc/db/courR14-ISO8859-1.pil"

url = "http://webware.lysator.liu.se/jc/wotsap/"
# It seems like we get URLs in latin-1 (or maybe latin-9, I haven't
# tried euro sign.)
urlencoding = 'iso-8859-15'

minsize = 50,50
maxsize = 2000,2000

from WebKit.Page import Page
import sys
# For some strange reason, I couldn't name the module wotsap. 
# Something about the context having the same name, I guess.
import wotsap_module

wot_large  = wotsap_module.Wot(dumpfile,   fontfile)
wot_debian = wotsap_module.Wot(debiandump, fontfile)

def findpaths(wot, bottom, top, config, file, setheader):
	paths = wot.findpaths(bottom, top, config, 'PIL')
        if not paths:
            return error(file, "Unable to find path from %s to %s." %\
			 (bottom, top))
	setheader( 'Content-type', 'image/png' )
        paths.save(file, 'png')

def keyinfo(wot, key, file, setheader):
    info = wot.keystats(key)
    if info:
        setheader( 'Content-type', 'text/plain' )
        file.write(info.encode('iso-8859-15', 'replace'))
    else:
        return error(file, "Unable to find key %s." % key)
        
def statistics(wot, file, setheader):
    setheader( 'Content-type', 'text/plain' )
    file.write(wot.wotstats())

def error(file, str):
    file.response().setHeader( 'Content-type', 'text/plain' )
    file.write("error: ")
    file.write(str.encode('iso-8859-15', 'replace'))
    file.write("\n")

# Filter and sort arguments
# This isn't really necessary, but if people are going to start
# linking to images, they will run into problems when the list order
# and moon phase changes, to their search terms matches another key.
def redirect(fields, sendredirect, urlencode):
    str = url + "?"
    for arg in ["top", "bottom", "size",
                "arrowlen", "arrowang", "colors", "wot"]:
        if fields.get(arg, None):
            str += arg + "="+urlencode(fields[arg])+"&"
    str = str[:-1]
    sendredirect(str)


class Main(Page):

    def writeHTML(self):
        request  = self.request()
        response = self.response()
        fields   = request.fields()

        wot = fields.get("wot", "large")
        if wot == "debian":
            wot = wot_debian
        else:
            wot = wot_large


        for arg in ["bottom", "top"]:
            if fields.has_key(arg):
                fields[arg] = unicode(fields[arg], urlencoding)

        bottom = fields.get("bottom", None)
        top    = fields.get("top",    None)

        keybottom=keytop=None
        if bottom:
            keybottom = wot.nametokey(bottom)
            if not keybottom:
                return error(self, "Unable to find key matching %s." % bottom)
        if top:
            keytop    = wot.nametokey(top)
            if not keytop:
                return error(self, "Unable to find key matching %s." % top)
        if bottom != keybottom or top != keytop:
            fields["bottom"] = keybottom
            fields["top"]    = keytop
            return redirect(fields, response.sendRedirect, self.urlEncode)

        config = {}

        if fields.has_key("size"):
            sizestr = fields["size"]
            size    = sizestr.split('x')
            if len(size) != 2:
                return error(self, 'Size must be in format "1024x768".')
            try:
                size = (int(size[0]), int(size[1]))
            except ValueError:
                return error(self, 'Size must be in format "1024x768".')
            if not minsize[0] <= size[0] <= maxsize[0] or not\
                   minsize[1] <= size[1] <= maxsize[1]:
                return error(self, 'Size too large or too small: %s'%sizestr)
            config["size"] = size

        try:
	    for f in ["arrowlen", "arrowang"]:
	        if fields.has_key(f):
                    config[f] = int(fields[f])
        except ValueError:
            return error(self, "Illegal integer %s." % fields[f])

        if fields.has_key("colors"):
            s = fields["colors"]
            colors = []
            try:
                if len(s) > wot.avail_colors*6:
                    raise ValueError
                while len(s) >= 6:
                    colors.append(int(s[0:2], 16))
                    colors.append(int(s[2:4], 16))
                    colors.append(int(s[4:6], 16))
                    s = s[6:]
                if len(s):
                    raise ValueError
            except ValueError:
                return error(self, "Illegal colormap: %s\n" % s +\
			     "Colormap should be specified as a number "+\
			     "of 3-byte (RGB) colors, written as\n"+\
			     "6 hexadecimal characters.\n")
            config["colors"] = colors
        
        if top and bottom:
            return findpaths(wot, bottom, top, config,
                             self, response.setHeader)
        if top:
            return keyinfo(wot, top, self, response.setHeader)

        return statistics(wot, self, response.setHeader)
