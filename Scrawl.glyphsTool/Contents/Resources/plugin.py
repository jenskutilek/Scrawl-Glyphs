# encoding: utf-8
from __future__ import division, print_function

import objc
from math import floor
from GlyphsApp import GSOFFCURVE, GSQCURVE, GSCURVE
from GlyphsApp.plugins import *

from AppKit import NSBezierPath, NSClassFromString, NSColor, NSData, NSGraphicsContext, NSImage, NSImageInterpolationNone, NSMakeRect, NSRoundLineCapStyle


plugin_id = "de.kutilek.scrawl"
default_pen_size = 1
default_pixel_size = 10


def initImage(layer, pixel_size=default_pixel_size):
	upm = layer.parent.parent.upm
	pad = int(round(upm / 10))
	w = int(round((2 * pad + layer.width) / pixel_size))
	h = int(round((2 * pad + upm) / pixel_size))
	img = NSImage.alloc().initWithSize_((w, h))
	# DEBUG: Draw a red rectangle around the image
	#img.lockFocus()
	#NSColor.redColor().set()
	#NSBezierPath.setLineWidth_(1)
	#NSBezierPath.strokeRect_(NSMakeRect(0, 0, w, h))
	#img.unlockFocus()
	return img


def getScrawl(layer):
	pen_size = layer.userData["%s.size" % plugin_id]
	if pen_size is None:
		pen_size = default_pen_size # scrawl pixels

	pixel_size = layer.userData["%s.unit" % plugin_id]
	if pixel_size is None:
		pixel_size = default_pixel_size # font units

	data = layer.userData["%s.data" % plugin_id]
	if data is None:
		data = initImage(layer, default_pixel_size)
	else:
		try:
			data = NSImage.alloc().initWithData_(data)
		except:
			data = initImage(layer, default_pixel_size)

	return pen_size, pixel_size, data


def setScrawl(layer, pen_size, pixel_size, data=None):
	layer.userData["%s.size" % plugin_id] = int(round(pen_size))
	layer.userData["%s.unit" % plugin_id] = int(round(pixel_size))
	if data is None:
		del layer.userData["%s.data" % plugin_id]
	else:
		tiff = data.TIFFRepresentation()
		print("Saving %i bytes ..." % len(tiff))
		layer.userData["%s.data" % plugin_id] = tiff


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

		# Create Vanilla window and group with controls
		viewWidth = 180
		viewHeight = 42
		self.sliderMenuView = Window((viewWidth, viewHeight))
		self.sliderMenuView.group = Group((0, 0, viewWidth, viewHeight))
		self.w = self.sliderMenuView.group
		y = 0
		self.w.text = TextBox((20, y, -20, 17), "%s Pen Size" % self.name)
		y += 18
		self.w.pen_size = Slider((20, y, -20, 24),
			minValue = 1,
			maxValue = 100,
			value = float(self.slider_value),
			tickMarkCount = 0,
			#stopOnTickMarks = False,
			#continuuous = True,
			callback=self.slider_callback,
			sizeStyle = 'small',
		)

		self.generalContextMenus = [
			{"view": self.sliderMenuView.group.getNSView()},
			{"name": Glyphs.localize({'en': u'Delete Scrawl', 'de': u'Gekritzel löschen'}), "action": self.delete_data},
		]
		self.keyboardShortcut = 'c'
		self.pen_size = default_pen_size
		self.pixel_size = default_pixel_size
		self.data = None
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
		if self.data is None:
			return
		font = layer.parent.parent
		pad = int(round(font.upm / 10))
		try:
			master = layer.parent.parent.masters[layer.layerId]
		except KeyError:
			return
		if master is None:
			return
		rect = NSMakeRect(-pad, master.descender - pad, 2 * pad + layer.width, 2 * pad + font.upm)
		NSGraphicsContext.saveGraphicsState()
		NSGraphicsContext.currentContext().setImageInterpolation_(NSImageInterpolationNone)
		self.data.drawInRect_(rect)
		NSGraphicsContext.restoreGraphicsState()

	def keyDown_(self, event):
		# Toggle between draw and eraser mode
		if event.characters() == "e":
			self.erase = not(self.erase)
		else:
			objc.super(ScrawlTool, self).keyDown_(event)

	def setPixel(self, event, dragging=False):
		if self.data is None:
			return
		try:
			editView = self.editViewController().graphicView()
		except:
			return
		
		layer = editView.activeLayer()
		try:
			master = layer.parent.parent.masters[layer.layerId]
		except KeyError:
			return
		if master is None:
			return
		
		Loc = editView.getActiveLocation_(event)
		pad = int(round(layer.parent.parent.upm / 10))
		loc_pixel = (
			(Loc.x + pad) / self.pixel_size,
			(Loc.y + pad - master.descender) / self.pixel_size
		)
		if self.prev_location is None or self.prev_location != loc_pixel:
			#print(loc_pixel)
			x, y = loc_pixel
			self.data.lockFocus()
			if self.erase:
				NSColor.whiteColor().set()
			else:
				NSColor.darkGrayColor().set()
			if dragging and self.prev_location is not None:
				px, py = self.prev_location
				path = NSBezierPath.alloc().init()
				NSBezierPath.setLineCapStyle_(NSRoundLineCapStyle)
				NSBezierPath.setLineWidth_(self.pen_size)
				#path.strokeLineFromPoint_toPoint_(x, y, x + self.pen_size, y + self.pen_size)
				path.moveToPoint_((px, py))
				path.lineToPoint_((x, y))
				path.stroke()
			else:
				half = self.pen_size / 2
				rect = NSMakeRect(
					x - half,
					y - half,
					self.pen_size,
					self.pen_size
				)
				path = NSBezierPath.bezierPathWithOvalInRect_(rect)
				path.fill()
			# For rectangular pens:
			#NSBezierPath.fillRect_(rect)
			self.data.unlockFocus()
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
		self.setPixel(event, True)
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

	def delete_data(self, sender=None):
		for layer in Glyphs.font.selectedLayers:
			deleteScrawl(layer)
		self.updateView()

	def slider_callback(self, sender=None):
		if sender is not None:
			self.pen_size = int("%i" % sender.get())
			self.updateView()
