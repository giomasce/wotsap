#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Pks2wot, create .wot file from pks server.
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


# The name of the keyserver. Will appear in the .wot's README file.
servername = "Local server (http://localhost:11371/)"

# Some keys in the strong set to start from.
startkeys  = [0xE8C80C34, 0xED9547ED, 0xFAEBD5FC, 0xD23450F9]

# The pks database
pksdb      = "/large/jc_pks/db/"

# Where to save to save the .wot file.
savefile   = "/large/jc_pks/test/dump-large.wot"

# How often to give feedback while fetching signatures.
printevery = 100

import sys
import os
import string
import locale
import struct
import time
import random

# It should be possible to add a new flag to pksclient to keep it from
# looking up names of signatures. That might make the indexing faster.
pksflags  = "vs"
# Use this line to run without logging and transactions. Faster, but
# less safe. Use only if noone else is accessing the database.
#pksflags  = "tvs"

pksclient = "/usr/sbin/pksclient"

def key2str(key):
    """Transforms a key given as integer to string"""
    return "0x" + string.zfill(hex(key)[2:], 8).upper()

# This is the slow part. To make this work on keyservers with
# something other than pksclient, this is the function to change. It
# should return a string containing a name and a dictionary with the
# keys signing this key as the dictionary keys. The dictionary values
# should be None. If key is invalid, return None.
def getsinglekeyfrompks(db, key):
    """Get a key name and signatures through pksclient"""

    # Call pksclient
    reply = os.popen("%s %s index %s %s 2>/dev/null"
                     % (pksclient, db, key2str(key), pksflags))
    topline = reply.readline()
    # We don't want pksclient to be blocked. Get all lines
    # immediately.
    lines = reply.readlines()
    reply.close()

    # Should not happen unless a key disappears under us.
    if topline == "":  
        print 'Illegal key %s' % key2str(key)
        sys.stdout.flush()
        return None

    # Get the name
    name = topline.split(None, 3)[3][:-1]
    if name == "*** KEY REVOKED ***":
        print "Key %s is revoked. Ignoring key" % key2str(key)
        sys.stdout.flush()
        return None
    if name == "":
        print "Key %s has empty name. Ignoring key" % key2str(key)
        sys.stdout.flush()
        return None

    # Iterate over the lines in pksclient output TODO: What if someone
    # inserts a key with a name that includes \n? Can pksclient handle
    # that in a reasonable way?
    signatures = {}
    for line in lines:
        lineparts = line.split()
        # Not all lines are interesting.
        if len(lineparts) >= 3 and \
               lineparts[0] == "sig" and \
               lineparts[2:] != \
               "(Unknown signator, can't be checked)".split() and \
               lineparts[2:] != "*** KEY REVOKED ***".split() and \
               lineparts[1]  != "00000000":
            signatures[int("0x"+lineparts[1], 0)] = None
    # Keys must be self-signed.
    if key not in signatures:
        print "Key %s has no self-signature. Ignoring key." \
              % key2str(key)
        return None
    else:
        del signatures[key]
    return name, signatures

# The same as the function above, but use a dictionary instead of
# external pksclient, and don't return names.
def getkeyfromdict(dict, key):
    """Get key signatures from a dictionary"""
    if dict.has_key(key):
        return None, dict[key]
    else:
        return None

def getwot(startkeys, getkeyfunc, getkeyarg, slow=0):
    """Get the whole strong set. Can take some time to complete"""

    # {key: [keys,signed,by,key], ...}
    sigdict  = {}
    # {key: "Owner of this key", ...}
    namedict = {}
    # List of all keys we know we have to check.
    keystocheck = {}
    for key in startkeys:
        keystocheck[key] = None
    # List of seen keys.
    seenkeys = {}

    while keystocheck:
        key = keystocheck.popitem()[0]
        if slow and len(namedict)%printevery == 0:
            print "Keys fetched/seen/in queue: %5d/%5d/%5d. Now fetching: %s"\
                  % (len(namedict), len(seenkeys),
                     len(keystocheck), key2str(key))
            sys.stdout.flush()

        ret = getkeyfunc(getkeyarg, key)

        # Don't bother with broken and unsigned keys
        if not ret:
            continue
        namedict[key], sigdict[key] = ret
        for x in sigdict[key]:
            if x not in seenkeys:
                keystocheck[x] = None
        seenkeys.update(sigdict[key])
    return (sigdict, namedict)

def reversesigs(sigdict):
    """Reverse signatures. (s/signs/signed by/)"""
    revsigdict = {}
    for key in sigdict:
        for sig in sigdict[key]:
            if sig not in revsigdict:
                revsigdict[sig] = {}
            revsigdict[sig][key] = None
    return revsigdict

def writetofile(savefilename, sigs, names, keys,
                begintime, endtime, servername):
    """Save .wot file. File format is documented at:
    http://www.lysator.liu.se/~jc/wotsap/wotfileformat.txt"""

    file = os.popen('bzip2 >"%s"' % savefilename, 'w')
    # Write .ar header
    file.write("!<arch>\n")

    def writearfileheader(filename, size):
        file.write("%-16s%-12s%-6s%-6s%-8s%-10s`\n" % \
               (filename + '/', int(time.time()),
                0, 0, 100644, size))

    def writearfile(filename, string):
        writearfileheader(filename, len(string))
        file.write(string)
        if len(string) & 1:
            file.write('\n')

    # Write file "README"
    str = \
        " README\n"\
        "This is a Web of Trust archive."                           "\n"\
        "The file format is documented at:"                         "\n"\
        "  http://www.lysator.liu.se/~jc/wotsap/wotfileformat.txt"  "\n"\
        ""                                                          "\n"\
        "It was extracted at the public key server %s."             "\n"\
        "Extraction started %s and ended %s."                       "\n"\
        % (servername,
           time.asctime(time.gmtime(begintime)) + " UTC",
           time.asctime(time.gmtime(  endtime)) + " UTC")
    writearfile("README", str)

    # Write file "WOTVERSION"
    writearfile("WOTVERSION", "0.1\n")

    # Write file "names"
    writearfile("names", string.join(names, '\n') + '\n')

    # Write file "keys"
    writearfileheader("keys", len(keys) * 4)
    for key in keys:
        file.write(struct.pack('!i', key))
    # No padding needed.

    # Write file "signatures"
    size=-4
    for siglist in sigs:
        size += (len(siglist)+1) * 4
    writearfileheader("signatures", size)
    for siglist in sigs[:-1]:
        for sig in siglist:
            file.write(struct.pack('!i', sig))
        file.write(struct.pack('!i', -1))
    for sig in sigs[-1]:
        file.write(struct.pack('!i', sig))  # No -1 on the end
    # No padding needed.

    file.close()

def toordered(sigdict, namedict):
    """Transform web to list format.
    To avoid people figuring out what key to falsely sign just to get on
    top of the list, we always randomize the order. For some strange
    reason, this also seems to give better compression."""

    keylist = sigdict.keys()
    random.shuffle(keylist)
    keydict = {}
    for x in xrange(len(keylist)):
        keydict[keylist[x]] = x
    siglist = range(len(sigdict))
    for x in keylist:
        siglist[keydict[x]] = [ keydict[y] for y in sigdict[x]]
        # Sort each signature list, for best compression
        siglist[keydict[x]].sort()
    namelist = [ namedict[key] for key in keylist ]
    return keylist, namelist, siglist


if __name__ == "__main__":
    begintime = time.time()
    print "Starting to fetch signatures from the key server."
    print "Now is %s local time." % time.ctime(begintime)
    print ""
    sys.stdout.flush()
    # This is the slow operation.
    (sigdict,namedict) = getwot(startkeys, getsinglekeyfrompks,
                                pksdb, slow=1)

    # Pickle/unpickle this intermediate state. Useful for debugging.
    #import cPickle
    #cPickle.dump((sigdict,namedict),  \
    #          open("/large/jc_pks/test/dump-large.bin", 'w'), 1)
    #(sigdict,namedict) = cPickle.load( \
    #          open("/large/jc_pks/test/dump-large.bin"))

    endtime = time.time()
    print ""
    print "Done fetching signatures."
    print "Now is %s local time." % time.ctime(endtime)
    print "Number of keys in backwards reachable set:", len(sigdict)
    sys.stdout.flush()

    # Process all keys again, in the other direction, to filter out
    # the strong set.
    sigdict = reversesigs(sigdict)
    sigdict = getwot(startkeys, getkeyfromdict, sigdict)[0]
    print "Number of keys in strong set: (backwards) ", len(sigdict)
    sigdict = reversesigs(sigdict)
    print "And forward. Should be the same:          ", len(sigdict)
    sys.stdout.flush()

    # Now, we want everything numbered. This means we have to use
    # lists instead of dictionaries.
    keylist, namelist, siglist = toordered(sigdict, namedict)

    print "Writing to file %s:" % savefile,
    sys.stdout.flush()
    writetofile(savefile, siglist, namelist, keylist,
                begintime, endtime, servername)
    print "Done."
