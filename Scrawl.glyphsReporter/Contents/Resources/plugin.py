# encoding: utf-8
from __future__ import division
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

import imp
try:
	imp.find_module('vanilla')
	can_display_ui = True
except ImportError:
	can_display_ui = False
	print "Please install vanilla to enable UI dialogs for Scrawl. You can install vanilla through Glyphs > Preferences > Addons > Modules."


plugin_id = "de.kutilek.Scrawl"




def getScrawl(layer):
	pixel_size = layer.userData["%s.unit" % plugin_id]
	if pixel_size is None:
		pixel_size = 1 # font units

	data = layer.userData["%s.data" % plugin_id]
	if data is None:
		data = []
	else:
		data = [(int(x), int(y)) for x, y in data]

	return pixel_size, data


def setGrid(layer, x, y=None, grid_type=None):
	if x is None:
		x = 0
	if x == 0:
		deleteGrid(layer)
		return
	if y is None:
		y = x
	layer.userData["%s.value" % plugin_id] = [x, y]
	if grid_type is None:
		if layer.userData["%s.type" % plugin_id] is not None:
			del layer.userData["%s.type" % plugin_id]
	else:
		layer.userData["%s.type" % plugin_id] = grid_type


def deleteScrawl(layer):
	for key in ("unit", "data", "size"):
		full_key = "%s.%s" % (plugin_id, key)
		if layer.userData[full_key] is not None:
			del layer.userData[full_key]




class ScrawlReporter(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({'en': u'Scrawl'})


	#def start(self):
	#	if can_display_ui:
	#		mainMenu = NSApplication.sharedApplication().mainMenu()
	#		s = objc.selector(self.editMasterGrid,signature='v@:')
	#		newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
	#			Glyphs.localize({
	#				'en': u"Master Grid…",
	#				'de': u'Master-Raster…'
	#			}),
	#			s,
	#			""
	#		)
	#		newMenuItem.setTarget_(self)
	#		submenu = mainMenu.itemAtIndex_(2).submenu()
	#		submenu.insertItem_atIndex_(newMenuItem, submenu.numberOfItems())

		
	def background(self, layer):

		# Check if the drawing should be shown
		
		currentController = self.controller.view().window().windowController()
		if currentController:
			tool = currentController.toolDrawDelegate()
			if tool.isKindOfClass_(NSClassFromString("GlyphsToolText")) or tool.isKindOfClass_(NSClassFromString("GlyphsToolHand")):
				return
		
		try:
			master = layer.parent.parent.masters[layer.layerId]
		except KeyError:
			return
		if master is None:
			return

		pixel_size, data = getScrawl(layer)


		NSColor.lightGrayColor().set()
		#NSBezierPath.setDefaultLineWidth_(0.6/self.getScale())
		for x, y in data:
			NSBezierPath.fillRect_(NSMakeRect(x * pixel_size, y * pixel_size, pixel_size, pixel_size))
		


	#def editMasterGrid(self):
	#	GridDialog()
