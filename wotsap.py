#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Web of trust statistics and pathfinder, Wotsap
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


defaultconfig = {
    "size":     (980, 700),
    "arrowlen": 15,
    "arrowang": 20,
    "colors":   [0x9d, 0xaf, 0x75,  # Background
                 0xc0, 0xc0, 0xff,  # Box interiors
                 0x00, 0x00, 0x00,  # Font
                 0x00, 0x00, 0x00,  # Lines
                 0x00, 0x90, 0x70,  # Arrows
                 0x00, 0x10, 0x70,  # Arrow borders
                 0xff, 0x00, 0x00,  # Box borders
                 0x00, 0x00, 0x00,  # Logo background
                 0xff, 0xff, 0xff]  # Logo foreground
    }
(col_bg, col_boxi, col_font, col_line, col_arrow,
 col_arrowb, col_boxb, col_end) = range(8)
col_logbs, col_logfs = "\x07", "\x08"
import sys
import os
import string
import struct
import math
import re
import Image, ImageDraw, ImageFont

packedlogo=[\
    528,1,6,1,3,1,13,1,2,1,27,1,17,1,15,1,1,1,21,1,7,1,8,1,15,1,20,1,6,1,6,1,
    3,1,13,1,2,1,27,1,17,1,15,1,23,1,16,1,15,1,20,1,6,1,1,2,2,3,1,3,1,1,1,2,3,
    1,2,1,2,1,1,1,2,1,2,1,1,1,2,1,2,1,1,1,2,1,2,1,4,1,1,1,2,1,2,2,2,3,2,3,2,3,
    2,1,1,1,4,1,1,1,1,1,2,1,5,2,3,2,3,1,8,1,2,2,3,1,1,1,2,1,2,1,2,3,2,3,2,2,2,
    3,2,1,1,2,3,1,7,2,2,1,2,1,3,1,2,2,2,1,5,1,2,1,1,1,2,1,2,1,1,1,2,1,2,1,1,1,
    2,1,2,1,4,1,1,1,2,1,1,1,2,1,4,1,2,1,2,1,3,1,1,2,5,1,1,1,1,1,2,1,4,1,2,1,1,
    1,2,1,2,1,2,2,2,1,1,1,1,1,2,1,2,1,1,1,2,1,2,1,1,1,3,1,2,1,2,1,2,1,4,1,1,2,
    2,1,2,1,7,1,3,1,2,1,3,1,2,1,3,1,5,1,2,1,2,1,1,1,1,1,3,1,1,1,1,1,3,1,1,1,1,
    1,5,1,1,1,1,1,3,2,3,3,2,1,2,1,3,1,1,1,6,1,1,1,1,1,2,1,5,2,2,4,2,1,1,1,2,2,
    2,1,1,1,5,1,2,1,1,1,1,1,2,1,3,1,2,1,3,2,3,3,1,1,3,1,2,1,7,1,3,1,2,1,3,1,2,
    1,3,1,5,1,2,1,2,1,1,1,1,1,3,1,1,1,1,1,3,1,1,1,1,1,5,1,1,1,1,1,5,1,1,1,2,1,
    2,1,2,1,3,1,1,1,6,1,1,1,1,1,2,1,7,1,1,1,5,1,8,1,1,1,5,1,2,1,1,1,1,1,2,1,3,
    1,2,1,5,1,1,1,2,1,1,1,3,1,2,1,7,1,3,1,2,1,3,1,2,2,2,1,4,1,2,1,4,1,1,1,5,1,
    1,1,5,1,1,1,6,1,2,2,2,1,2,1,1,1,2,1,2,1,2,1,3,1,1,1,6,1,1,1,1,1,2,1,4,1,2,
    1,1,1,2,1,1,1,9,1,1,1,2,1,1,1,4,1,1,1,3,1,3,1,2,1,2,1,2,1,1,1,2,1,1,2,2,1,
    1,1,8,1,3,1,2,2,2,2,1,1,1,2,3,1,1,1,2,1,4,1,1,1,5,1,1,1,5,1,1,1,4,1,1,1,2,
    1,4,2,3,2,1,1,1,2,2,3,2,1,4,1,1,1,1,1,2,3,2,1,2,2,3,2,2,1,9,1,2,2,2,1,4,1,
    1,1,4,3,3,2,2,2,3,2,1,2,1,2,2,1,22,1,44,1,60,1,1,1,37,1,28,1,43,1,62,1,38,
    1,361]

logo = []
curcol, othercol = col_logbs, col_logfs
for x in packedlogo:
    logo.append(curcol*x)
    curcol, othercol = othercol, curcol

del packedlogo
logo = Image.fromstring('P', (175,15), string.join(logo, ""))


# Terminology: Given key X, up (UP) in the web is the keys that
# are signed by X. Down (DN) is the keys that has signed X. To find
# the keys you might trust, you search up from your key. To find
# out who might trust you, you search down from your key.
UP, DN = range(2)

def loadfile(filename):
    """Load file as specified by
    http://www.lysator.liu.se/~jc/wotsap/wotfileformat.txt"""
    def error(str):
        print >>sys.stderr, "wotsap:", str
        sys.exit(1)

    try:
        f = open(filename)
    except IOError, (errno, strerror):
        error('Unable to open file "%s": %s' % (filename, strerror))

    header = "!<arch>\n"
    try:
        s = f.read(len(header))
    except IOError, (errno, strerror):
        error('Unable to read from file "%s": %s' % (filename, strerror))

    if s != header:
        f = os.popen('bunzip2 < "%s"' % filename)
        s = f.read(len(header))
        if s != header:
            error("%s does not look like a .wot file." % filename)

    sigs=names=keys=0
    readme=None
    while (not sigs) or (not names) or (not keys):
        filename, mtime, uid, gid, mode, size, trailer = \
        f.read(16), int(f.read(12)), int(f.read(6)), \
        int(f.read(6)), int(f.read(8)), int(f.read(10)), f.read(2)

        if trailer != '`\n':
            error("Corrupt WOT file, trailer not found.")
        filename = filename.split('/')[0]

        if filename == "README":
            readme = f.read(size)
            if size & 1:
                f.read(1)
        elif filename == "names":
            names = unicode(f.read(size), 'utf-8', errors='replace') \
                       .split('\n')
            if size & 1:
                f.read(1)
            # If the last name has a newline (as it should have):
            if names[-1] == "":
                del names[-1]
        elif filename == "keys":
            keys = []
            for n in xrange(size/4):
                keys.append(struct.unpack('!i', f.read(4))[0])
        elif filename == "WOTVERSION":
            version = f.read(size)
            if size & 1:
                f.read(1)
            if version != "0.1\n" and version[:4] != "0.1.":
                error("Unknown WOT file version %s" % version)
        elif filename == "signatures":
            current = {}
            sigs = [current]
            for n in xrange(size/4):
                key = struct.unpack('!i', f.read(4))[0]
                if key != 0xffffffff:
                    current[key] = None
                else:
                    current = {}
                    sigs.append(current)
        else:
            print >>sys.stderr, "Strange. Found %s file." % filename
            f.seek(size + (size&1), 1)
    f.close()
    if not (len(names) == len(keys) == len(sigs)):
        error("Corrupt WOT file: Number of keys/names/sigs does not match: %s"\
              % (len(keys), len(names), len(sigs)))
    return names, keys, sigs, readme

def reversesigs(sigs):
    """Reverse signatures. (s/signs/signed by/)
    Assumes the reversed set is of equal size <=> the set is a strongly
    connected set."""

    revsigs = [ {} for x in sigs ]
    for n in xrange(len(sigs)):
        for key in sigs[n]:
            revsigs[key][n] = None
    return revsigs

def findnext(keys, forbidden, web):
    """Return a dictionary containing keys and a set of keys link to."""
    connections = {}
    for x in keys:
        for y in web[x]:
            if y not in forbidden:
                if y not in connections:
                    connections[y] = {}
                connections[y][x] = None
    return connections

def findpaths(wot, bottom, top):
    """Find all paths in wot from bottom to top"""
    if bottom == top:
        return [{bottom: None}]
    seen = {bottom: None}
    conn = [{bottom: None}]
    for lev in xrange(30):
        conn.append(findnext(conn[lev], seen, wot.sigs[UP]))
        if top in conn[-1]:
            ret = [{top: None}]
            conn.reverse()
            conn.pop()
            for w in conn:
                ret.append( findnext(ret[-1], [], w ))
            return ret
        if len(conn[-1]) == 0:
            return None
        seen.update(conn[-1])

# Currently unused.
def msd(wot, key):
    """Quite fast msd checker, but not fast enough to calculate all msds at
    startup."""

    seen = {key: None}
    lastlevel = {key: None}
    total = 0
    for lev in xrange(30):
        total += lev * len(lastlevel)
        thislevel = {}
        for x in lastlevel:
            thislevel.update(wot.sigs[DN][x])
        lastlevel = {}
        for x in thislevel:
            if x not in seen:
                lastlevel[x] = None
        seen.update(lastlevel)
        if not lastlevel:
            break
    return float(total) / len(wot.keys)

def key2str(key):
    """Transforms a key given as integer to string"""
    return string.zfill(hex(key)[2:], 8).upper()

def fullkey(wot, key):
    """Transform key to string with both keyID and name"""
    return u"0x%s %s" % (key2str(wot.keys[key]), wot.names[key])

def keystats(wot, key):
    """Statistics about a key"""
    seen = {key: None}
    conn = {key: None}
    total = 0
    header = u"Statistics for key %s\n" % fullkey(wot, key)
          
    downtrace = \
     "Tracing downwards from this key. Keys in level 1 have signed this\n"\
     "key, keys in level (n) have signed at least one key in level (n-1).\n\n"
    smalllevels = "Levels with 10 keys or less:\n"
    for lev in xrange(30):
        if len(conn) <= 10:
            smalllevels += "  Level %2d:\n" % lev
            for x in conn:
                smalllevels += "    %s\n" % fullkey(wot, x)
        total += lev * len(conn)
        downtrace += "Keys in level %2d: %6d\n" % (lev, len(conn))
        conn = findnext(conn, seen, wot.sigs[DN])
        if not conn:
            break
        seen.update(conn)
    msd  = "Mean shortest distance:                  %2.4f\n" % \
           (float(total) / len(wot.keys))
    msd += "Total number of keys in strong set: %6d\n\n" % len(wot.keys)
    n, a = len(wot.sigs[DN][key]), (float(wot.numofsigs) / len(wot.keys))
    msd += "This key is signed by %d key" % n
    if n != 1:
        msd += "s"
    msd += ", which is "
    if n > a:
        msd += "more than"
    elif n==a:
        msd += "equal to"
    else:
        msd += "less than"
    msd += " the average %2.4f.\n"   % a
    msd += "This key has signed %d key" % len(wot.sigs[UP][key])
    if len(wot.sigs[UP][key]) != 1:
        msd += "s"
    msd += ".\n"
    
    footer = "Another report for this key is available at:\n" \
             "  http://keyserver.kjsl.com/~jharris/ka/current/%s/%s\n" \
             "But note that that report in updated about once every month,\n"\
             "and it counts paths to the whole reachable set, while the\n"\
             "above is calculated from the strongly connected set. Your msd\n"\
             "might differ.\n"%\
             (key2str(wot.keys[key]).upper()[:2],\
              key2str(wot.keys[key]).upper())

    ups  = "This key is signed by:\n"
    keys = wot.sigs[DN][key]
    for x in keys:
        ups += u"  %s\n" % fullkey(wot, x)
    ups += "Total: %d key" % len(keys)
    if len(keys) != 1:
        ups += "s"
    ups += ".\n"
    ups += "\n"
    ups += "Keys signed by this key:\n"
    keys = wot.sigs[UP][key]
    for x in keys:
        ups += u"  %s\n" % fullkey(wot, x)
    ups += "Total: %d key" % len(keys)
    if len(keys) != 1:
        ups += "s"
    ups += ".\n"

    return header+'\n'+downtrace+'\n'+smalllevels+'\n'+msd+'\n'+ups+'\n'+footer
    

(top, middle, bottom) = (-0.5, 0, 0.5)
def yposition(pos, numlevels, where, boxh, height):
    return float(boxh)/2+(pos+0.5)*(height-boxh)/numlevels + where*boxh

# To create anything other than PNG, like SVG or text, these two are
# the functions to change.
def drawline(draw, x0, y0, x1, y1, config):
    """Draw an arrow in a PIL object"""
    draw.line( [x0, y0, x1, y1], fill=col_line )
    x=x0-x1
    y=y0-y1
    a = config["arrowang"] * 2*math.pi / 360
    s = config["arrowlen"] / math.sqrt((x**2)+(y**2))
    # Rotation and scaling matrix:
    rotm = [ math.cos(a)*s, math.sin(a)*s,
            -math.sin(a)*s, math.cos(a)*s]
    rot0 = (rotm[0]*x+rotm[1]*y ,  rotm[2]*x+rotm[3]*y)
    rot1 = (rotm[0]*x-rotm[1]*y , -rotm[2]*x+rotm[3]*y)
    draw.polygon( [ (x1        , y1        ),
                    (x1+rot0[0], y1+rot0[1]),
                    (x1+rot1[0], y1+rot1[1])],
                  outline=col_arrowb, fill=col_arrow)

def drawnode(draw, x, y, w, h, key, wot):
    """Draw a node (key) in a PIL object."""
    draw.rectangle( (x,y,x+w,y+h), fill=col_boxi, outline=col_boxb)
    border = 2
    x += border
    y += border
    w -= border*2
    h -= border*2
    # What charset should we use?
    keystr = key2str(wot.keys[key])
    name = wot.names[key].encode('iso-8859-15', 'replace')
    lines = (keystr + '\n' + name.replace('<', '\n<')).split('\n')
    sizes = []
    totalheight = 0
    for l in xrange(len(lines)):
        lines[l] = lines[l].strip()
        while wot.font.getsize(lines[l])[0] > w:
            lines[l] = lines[l][:-1]
        sizes.append(wot.font.getsize(lines[l]))
        totalheight += sizes[-1][1]
    
    yoffset = (h - totalheight) / 2
    for l in xrange(len(lines)):
        xoffset  = (w - sizes[l][0])/2
        draw.text((x+xoffset, y+yoffset), lines[l],
                  font=wot.font, fill=col_font)
        yoffset += sizes[l][1]

def create_pil(web, keys, config, wot):
    """Create a PIL object with a graph of a web."""
    conf = defaultconfig.copy()
    if config:
        conf.update(config)

    size     = conf["size"]
    boxh  = wot.font.getsize('Al9F_-/\<>@"')[1] * 3.5
    im = Image.new('P', size);
    palette = [ 0 for x in xrange(768) ]
    palette[0:len(defaultconfig["colors"])] = defaultconfig["colors"]
    if config.has_key("colors"):
        palette[0:len(   config["colors"])] =        config["colors"]
    im.putpalette(palette)
    draw = ImageDraw.Draw(im)
    levels = len(web)
    # Calculate widths. Proportional to
    # number_of_links_up*number_of_links_down
    widths    = [[size[0]/2]]
    positions = [[size[0]/4]]
    for level in xrange(1, levels-1):
        numnodes = len(web[level])
        lu = [0 for x in range(numnodes)]
        ld = [0 for x in range(numnodes)]
        for x in xrange(len(web[level])):
            lu[x] = len(web[level][x])
        for x in web[level+1]:
            for y in x:
                ld[y] += 1
        w = [ x[0]*x[1] for x in zip(lu, ld)]
        tot = 0
        for x in w:
            tot += x
        # Pad with a total width as wide as the average node.
        pad = float(tot)/len(w)
        tot += pad
        # Adjust units to fit image
        pad *= size[0] / tot
        for x in xrange(len(w)):
            w[x] *= size[0] / tot
        # Calculate positions. Positions are always the _left_ corner.
        dist = pad / len(w)
        pos = dist/2
        p = []
        for x in xrange(len(w)):
            p.append(int(pos))
            pos += w[x] + dist
            w[x] = int(w[x])
        widths.append(w)
        positions.append(p)
    widths.append([size[0]/2])
    positions.append([size[0]/4])
    # Edges
    for level in xrange(1, levels):
        for xpos in xrange(len(web[level])):
            for pointto in web[level][xpos]:
                drawline(draw,
                         positions[level][xpos] +
                         widths[level][xpos]/
                             float(len(widths[level-1])+1) * (pointto+1)
                         ,
                         yposition(level,   levels, top,    boxh, size[1]),
                         positions[level-1][pointto] +
                         widths[level-1][pointto]/
                             float(len(widths[level])+1) * (xpos+1)
                         ,
                         yposition(level-1, levels, bottom, boxh, size[1]),
                         conf)
    # Nodes
    for level in xrange(levels):
        for xpos in xrange(len(web[level])):
            drawnode(draw,
                     positions[level][xpos],
                     yposition(level, levels, top, boxh, size[1]),
                     widths[level][xpos], boxh,
                     keys[level][xpos],
                     wot)
    im.paste(logo, (size[0]-logo.size[0]-10,
                    size[1]-logo.size[1]-10,))
    return im

def webtoordered(web):
    """Transform unordered web to one suitable for graphing."""
    webkeys = [web[0].keys()]
    webarrw = [[[]]]
    for level in xrange(1, len(web)):
        if len(web[level]) > 1:
            # A very simple edge crossing minimization heuristic: Give
            # number centered around 0 for each node. Close to center
            # of keys it links to, and close to the middle if many
            # edges on the other side.
            nodes = web[level].keys()
            nextlevellinks = []
            for x in web[level+1].values():
                nextlevellinks.extend(x.keys())
            center = (len(webkeys[level-1])-1) / 2.
            positions = []
            for node in nodes:
                pos = 0.
                for edgeto in web[level][node]:
                    pos += webkeys[level-1].index(edgeto)-center
                pos /= nextlevellinks.count(node)
                positions.append(pos)
            sorted = [x for x in positions]
            sorted.sort()
            keys = range(len(web[level]))
            pos = 0
            for x in sorted:
                index = positions.index(x)
                keys[pos] = nodes[index]
                positions[index] = None
                pos += 1
            webkeys.append(keys)
            webarrw.append([ [webkeys[level-1].index(x) for x in \
                              web[level][y]] for y in webkeys[level]])
        else:
            webkeys.append(web[level].keys())
            webarrw.append([ [webkeys[level-1].index(x) for x in \
                              web[level][y]] for y in webkeys[level]])
    return webkeys, webarrw


# This could be done a lot better. We could draw a text graph similar
# to the image created above.
def textweb(wot, web):
    """Graph a web using text only."""
    ret = ""
    for x in web:
        for y in x:
            if x[y]:
                ret += "%s  --> (signs:)\n" % fullkey(wot, y)
                for key in x[y].keys():
                    ret += "          " + fullkey(wot, key) + "\n"
            else:
                ret += "%s\n" % wot.names[y]
        ret += '\n'
    return ret

keyre = re.compile("^(0x)?[0-9a-fA-f]{8}$")
# We could do this much faster with a dictionary, but looping through
# all keys is fast enough, and saves some memory.
def nametokey(wot, name):
    """Search key from name"""
    name = name.strip()
    if keyre.search(name):
        if len(name) == 8:
            name = "0x" + name
        key = int(name, 0)
        if key in wot.keys:
            return wot.keys.index(key)
        else:
            return None
    else:
        words = name.lower().split()
        if len(words)==0:
            return 0
        for i in xrange(len(wot.names)):
            for word in words:
                if wot.names[i].lower().find(word) == -1:
                    break
            else:
                return i

def wotstats(wot):
    """Statistics about the whole WOT"""
    ret  = "Statistics for this Web of Trust:\n"
    ret += "Total number of keys:       %6d\n" % len(wot.keys)
    ret += "Total number of signatures: %6d\n" % wot.numofsigs
    ret += "Average signatures per key:      %2.4f\n" % \
           (float(wot.numofsigs) / len(wot.keys))
    ret += "\n"
    if wot.readme:
        ret += "The Web of Trust dump contained this README file:\n"
        ret += "\n"
        ret += wot.readme
    else:
        ret += "The Web of Trust dump contained no README file.\n"
    return ret

class Wot:
    def __init__(self, dumpfile, fontfile=None):
        if fontfile:
            self.initfont(fontfile)
        self.sigs = range(2)
        (self.names, self.keys, self.sigs[DN], self.readme) \
            = loadfile(dumpfile)
        self.sigs[UP] = reversesigs(self.sigs[DN])
        self.numofsigs = 0
        for x in self.sigs[UP]:
            self.numofsigs += len(x)

    avail_colors = col_end

    def initfont(self, fontfile):
        self.font = ImageFont.load(fontfile)

    def nametokey(self, name):
        key = nametokey(self, name)
        if key is not None:
            return "0x" + key2str(self.keys[key])

    def findpaths(self, bottom, top, config=None, format='txt'):
        bottom = nametokey(self, bottom)
        top    = nametokey(self, top   )
        if bottom is None or top is None:
            return None

        if format=='txt':
            return textweb(self, findpaths(self, bottom, top))
        elif format=='PIL':
            web = findpaths(self, bottom, top)
            (webkeys, webarrw) = webtoordered(web)
            return create_pil(webarrw, webkeys, config, self)
        else:
            raise ValueError

    def keystats(self, key):
        key = nametokey(self, key)
        if key is None:
            return None
        return keystats(self, key)

    def wotstats(self):
        return wotstats(self)

if __name__ == "__main__":
    import locale

    locale.setlocale(locale.LC_CTYPE, "")
    encoding = locale.nl_langinfo(locale.CODESET)

    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print >>sys.stderr, "Usage: %s filename.wot [key [key]]\n"%sys.argv[0]
        sys.exit(1)

    wot = Wot(sys.argv[1])

    if len(sys.argv) == 2:
        ret = wot.wotstats()
        if ret is not None:
            print ret.encode(encoding, 'replace')
        else:
            print >>sys.stderr, "Sorry, something went wrong."
    elif len(sys.argv) == 3:
        bottom = unicode(sys.argv[2], encoding, 'replace')
        ret = wot.keystats(bottom)
        if ret is not None:
            print ret.encode(encoding, 'replace')
        else:
            print >>sys.stderr, "Sorry, key %s not found." % sys.argv[2]
    else:
        bottom = unicode(sys.argv[2], encoding, 'replace')
        top    = unicode(sys.argv[3], encoding, 'replace')
        ret = wot.findpaths(bottom, top)
        if ret is not None:
            print ret.encode(encoding, 'replace')
        else:
            print >>sys.stderr, "Sorry, unable to find path."
