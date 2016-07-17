#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# This file is meant to be used with Webware (http://webware.sf.net/).

from WebKit.Page import Page
import sys

class Main(Page):

    def writeHTML(self):
        self.response().sendRedirect("http://www.lysator.liu.se/~jc/wotsap/")
