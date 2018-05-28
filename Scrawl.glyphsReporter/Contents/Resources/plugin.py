# encoding: utf-8
from __future__ import division, print_function

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *


from AppKit import NSClassFromString, NSGraphicsContext, NSImage, NSImageInterpolationNone, NSMakeRect


plugin_id = "de.kutilek.scrawl"




class ScrawlReporter(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({'en': u'Scrawl'})
		
	def background(self, layer):

		# Check if the drawing should be shown

		currentController = self.controller.view().window().windowController()
		if currentController:
			tool = currentController.toolDrawDelegate()
			if tool.isKindOfClass_(NSClassFromString("GlyphsToolText")) \
				or tool.isKindOfClass_(NSClassFromString("GlyphsToolHand")) \
				or tool.isKindOfClass_(NSClassFromString("ScrawlTool")):
				return
		
		# find master for image positioning (descender)
		
		try:
			master = layer.parent.parent.masters[layer.layerId]
		except KeyError:
			return
		if master is None:
			return
		
		# draw pixels

		data = layer.userData["%s.data" % plugin_id]
		if data is None:
			return
		try:
			data = NSImage.alloc().initWithData_(data)
		except:
			return
		font = layer.parent.parent
		pad = int(round(font.upm / 10))
		rect = NSMakeRect(-pad, master.descender - pad, 2 * pad + layer.width, 2 * pad + font.upm)
		NSGraphicsContext.saveGraphicsState()
		NSGraphicsContext.currentContext().setImageInterpolation_(NSImageInterpolationNone)
		data.drawInRect_(rect)
		NSGraphicsContext.restoreGraphicsState()
