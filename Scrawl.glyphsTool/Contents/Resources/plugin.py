# encoding: utf-8
from __future__ import division, print_function

import objc
from math import floor
from GlyphsApp import GSOFFCURVE, GSQCURVE, GSCURVE
from GlyphsApp.plugins import *

from AppKit import NSShiftKeyMask, NSString # NSEventModifierFlagShift


plugin_id = "de.kutilek.Scrawl"
default_pen_size = 1
default_pixel_size = 8


def getScrawl(layer):
	pen_size = layer.userData["%s.size" % plugin_id]
	if pen_size is None:
		pen_size = default_pen_size # scrawl pixels

	pixel_size = layer.userData["%s.unit" % plugin_id]
	if pixel_size is None:
		pixel_size = default_pixel_size # font units

	data = layer.userData["%s.data" % plugin_id]
	if data is None:
		data = set()
	else:
		try:
			data = set([(int(x), int(y)) for x, y in data])
		except:
			data = set()

	return pen_size, pixel_size, data


def setScrawl(layer, pen_size, pixel_size, data):
	layer.userData["%s.size" % plugin_id] = int(round(pen_size))
	layer.userData["%s.unit" % plugin_id] = int(round(pixel_size))
	layer.userData["%s.data" % plugin_id] = list(data)


def deleteScrawl(layer):
	for key in ("unit", "data", "size"):
		full_key = "%s.%s" % (plugin_id, key)
		if layer.userData[full_key] is not None:
			del layer.userData[full_key]




class ScrawlTool(SelectTool):
	
	def settings(self):
		from vanilla import ComboBox, Group, Slider, TextBox, Window 
		self.name = 'Scrawl'
		self.slider_value = 1 # current slider value
		#self.coordinates = GlyphCoordinates()
		#self.endPts = []
		self.axis_tag = "" # current axis tag
		self._axis_tags = []

		# Create Vanilla window and group with controls
		viewWidth = 180
		viewHeight = 68
		self.sliderMenuView = Window((viewWidth, viewHeight))
		self.sliderMenuView.group = Group((0, 0, viewWidth, viewHeight))
		self.w = self.sliderMenuView.group
		y = 0
		self.w.text = TextBox((20, y, -20, 17), self.name)
		y += 18
		self.w.pen_size = Slider((20, y, -20, 24),
			minValue = 1,
			maxValue = 10,
			value = float(self.slider_value),
			tickMarkCount = 0,
			#stopOnTickMarks = False,
			#continuuous = True,
			callback=self.slider_callback,
			sizeStyle = 'small',
		)


		self.generalContextMenus = [
			{"view": self.sliderMenuView.group.getNSView()}
		]
		self.keyboardShortcut = 'c'
		self.pen_size = default_pen_size
		self.pixel_size = default_pixel_size
		self.data = []
		self.prev_location = None
		self.erase = False

	def start(self):
		pass

	def activate(self):
		if Glyphs.font.selectedLayers:
			layer = Glyphs.font.selectedLayers[0]
			self.pen_size, self.pixel_size, self.data = getScrawl(layer)
			self.w.pen_size.set(self.pen_size)
			self.prev_location = None
			#deleteScrawl(layer)

	def deactivate(self):
		if Glyphs.font.selectedLayers:
			layer = Glyphs.font.selectedLayers[0]
			# save data
			setScrawl(layer, self.pen_size, self.pixel_size, self.data)
	
	def foreground(self, layer):
		pass

	def background(self, layer):
		# draw pixels
		NSColor.grayColor().set()
		for x, y in self.data:
			NSBezierPath.fillRect_(NSMakeRect(x * self.pixel_size, y * self.pixel_size, self.pixel_size, self.pixel_size))

	def keyDown_(self, event):
		# Toggle between draw and eraser mode
		if event.characters() == "e":
			self.erase = not(self.erase)
		else:
			objc.super(ScrawlTool, self).keyDown_(event)

	def setPixel(self, event):
		try:
			editView = self.editViewController().graphicView()
		except:
			return
		
		Loc = editView.getActiveLocation_(event)
		#layer = editView.activeLayer()
		#font = layer.font()
		
		loc_pixel = set([(
			int(floor(Loc.x / self.pixel_size)),
			int(floor(Loc.y / self.pixel_size))
		)])
		if self.prev_location is None or self.prev_location != loc_pixel:
			if self.erase:
				self.data = self.data - loc_pixel
			else:
				self.data = self.data | loc_pixel
			self.prev_location = loc_pixel

	def mouseDown_(self, event):
		if event.clickCount() == 3:
			self.mouseTripleDown_(event)
			return
		if event.clickCount() == 2:
			self.mouseDoubleDown_(event)
			return
		self.setPixel(event)
		self.updateView()
	
	def mouseDragged_(self, event):
		self.setPixel(event)
		self.updateView()
		
	def mouseUp_(self, event):
		self.setPixel(event)
		self.updateView()

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__

	def updateView(self):
		currentTabView = Glyphs.font.currentTab
		if currentTabView:
			currentTabView.graphicView().setNeedsDisplay_(True)

	def slider_callback(self, sender=None):
		if sender is not None:
			self.pen_size = "%i" % sender.get()
			self.updateView()
