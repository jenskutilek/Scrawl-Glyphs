# encoding: utf-8
from __future__ import division, print_function

import objc
from math import floor
from os.path import dirname, join
from GlyphsApp import GSOFFCURVE, GSQCURVE, GSCURVE, UPDATEINTERFACE
from GlyphsApp.plugins import *

from AppKit import NSBezierPath, NSBitmapImageRep, NSClassFromString, NSColor, NSData, NSDeviceWhiteColorSpace, NSGraphicsContext, NSImage, NSImageColorSyncProfileData, NSImageInterpolationNone, NSMakeRect, NSPNGFileType, NSPoint, NSRoundLineCapStyle, NSTIFFFileType


plugin_id = "de.kutilek.scrawl"
default_pen_size = 2
default_pixel_size = 2


def initImage(layer, pixel_size=default_pixel_size):
	upm = layer.parent.parent.upm
	pad = int(round(upm / 10))
	w = int(round((2 * pad + layer.width) / pixel_size))
	h = int(round((2 * pad + upm) / pixel_size))
	# See https://developer.apple.com/documentation/appkit/nsbitmapimagerep/1395538-init
	img = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bitmapFormat_bytesPerRow_bitsPerPixel_(
		None,   # BitmapDataPlanes
		w,      # pixelsWide
		h,      # pixelsHigh
		8,      # bitsPerSample: 1, 2, 4, 8, 12, or 16
		1,      # samplesPerPixel: 1 - 5
		False,  # hasAlpha
		False,  # isPlanar
		NSDeviceWhiteColorSpace,  # colorSpaceName
		0,      # bitmapFormat
		0,      # bytesPerRow
		0,      # bitsPerPixel
	)
	"""
		NSCalibratedWhiteColorSpace
		NSCalibratedBlackColorSpace
		NSCalibratedRGBColorSpace
		NSDeviceWhiteColorSpace
		NSDeviceBlackColorSpace
		NSDeviceRGBColorSpace
		NSDeviceCMYKColorSpace
		NSNamedColorSpace
		NSCustomColorSpace
	"""
	# The image is filled black for some reason, make it white
	current = NSGraphicsContext.currentContext()
	context = NSGraphicsContext.graphicsContextWithBitmapImageRep_(img)
	NSGraphicsContext.setCurrentContext_(context)
	NSColor.whiteColor().set()
	#NSBezierPath.setLineWidth_(1)
	NSBezierPath.fillRect_(NSMakeRect(0, 0, w, h))
	NSGraphicsContext.setCurrentContext_(current)
	return img




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
			{"name": Glyphs.localize({'en': u'Save Scrawl To Background Image', 'de': u'Gekritzel als Hintergrundbild speichern'}), "action": self.save_background},
		]
		self.keyboardShortcut = 'c'
		self.pen_size = default_pen_size
		self.pixel_size = default_pixel_size
		self.data = None
		self.prev_location = None
		self.erase = False
		self.mouse_position = None
		self.layer = None
		self.needs_save = False
		self.current_layer = self.get_current_layer()

	def start(self):
		pass

	def get_current_layer(self):
		try:
			editView = self.editViewController().graphicView()
		except:
			return None
		return editView.activeLayer()

	def activate(self):
		self.current_layer = self.get_current_layer()
		if self.current_layer is not None:
			self.loadScrawl()
			self.w.pen_size.set(self.pen_size)
			self.prev_location = None
		Glyphs.addCallback(self.update, UPDATEINTERFACE)

	def deactivate(self):
		Glyphs.removeCallback(self.update)

	def foreground(self, layer):
		try:
			self.mouse_position = self.editViewController().graphicView().getActiveLocation_(Glyphs.currentEvent())
		except:
			self.logToConsole( "foreground: mouse_position: %s" % str(e) )
			self.mouse_position = None
			return

		if self.mouse_position is not None:
			x, y = self.mouse_position
			scaled_pen = self.pen_size * self.pixel_size
			half = scaled_pen / 2
			rect = NSMakeRect(
				x - half,
				y - half,
				scaled_pen,
				scaled_pen
			)
			path = NSBezierPath.bezierPathWithOvalInRect_(rect)
			path.setLineWidth_(1)
			if self.erase:
				NSColor.redColor().set()
			else:
				NSColor.lightGrayColor().set()
			path.stroke()

	def background(self, layer):
		self.layer = layer
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
			self.updateView()
		elif event.characters() in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
			self.pen_size = int(event.characters()) * self.pixel_size
		else:
			objc.super(ScrawlTool, self).keyDown_(event)

	def setPixel(self, event, dragging=False):
		if self.data is None:
			return False
		try:
			editView = self.editViewController().graphicView()
		except:
			return False
		
		layer = editView.activeLayer()
		try:
			master = layer.parent.parent.masters[layer.layerId]
		except KeyError:
			return False
		if master is None:
			return False
		
		Loc = editView.getActiveLocation_(event)
		pad = int(round(layer.parent.parent.upm / 10))
		loc_pixel = (
			(Loc.x + pad) / self.pixel_size,
			(Loc.y + pad - master.descender) / self.pixel_size
		)
		if self.prev_location is None or self.prev_location != loc_pixel:
			x, y = loc_pixel
			current = NSGraphicsContext.currentContext()
			context = NSGraphicsContext.graphicsContextWithBitmapImageRep_(self.data)
			if context is None:
				self.prev_location = loc_pixel
				print("Could not get context in setPixel")
				return False
			NSGraphicsContext.saveGraphicsState()
			NSGraphicsContext.setCurrentContext_(context)
			if self.erase:
				NSColor.whiteColor().set()
			else:
				NSColor.blackColor().set()
			if dragging and self.prev_location is not None:
				px, py = self.prev_location
				path = NSBezierPath.alloc().init()
				NSBezierPath.setLineCapStyle_(NSRoundLineCapStyle)
				NSBezierPath.setLineWidth_(self.pen_size)
				#path.strokeLineFromPoint_toPoint_(x, y, x + self.pen_size, y + self.pen_size)
				path.moveToPoint_((px, py))
				path.lineToPoint_((x, y))
				path.stroke()
				self.needs_save = True
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
				self.needs_save = True
			# For rectangular pens:
			#NSBezierPath.fillRect_(rect)
			NSGraphicsContext.setCurrentContext_(current)
			NSGraphicsContext.restoreGraphicsState()
			self.prev_location = loc_pixel
		return True

	def mouseDown_(self, event):
		if event.clickCount() == 3:
			self.mouseTripleDown_(event)
			return
		if event.clickCount() == 2:
			self.mouseDoubleDown_(event)
			return
		if self.setPixel(event):
			self.updateView()
	
	def mouseDragged_(self, event):
		if self.setPixel(event, True):
			self.updateView()
		
	def mouseUp_(self, event):
		if self.setPixel(event):
			if self.needs_save:
				self.saveScrawl()
				self.updateView()

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__

	def update(self, sender=None):
		cl = self.get_current_layer()
		if cl != self.current_layer:
			if self.needs_save:
				self.saveScrawl()
			self.current_layer = cl
			self.loadScrawl()
			self.w.pen_size.set(self.pen_size)
			self.prev_location = None
		self.updateView()

	def updateView(self):
		currentTabView = Glyphs.font.currentTab
		if currentTabView:
			currentTabView.graphicView().setNeedsDisplay_(True)

	def delete_data(self, sender=None):
		for layer in Glyphs.font.selectedLayers:
			deleteScrawl(layer)
		self.updateView()

	def save_background(self, sender=None):
		for layer in Glyphs.font.selectedLayers:
			saveScrawlToBackground(layer)

	def slider_callback(self, sender=None):
		if sender is not None:
			self.pen_size = int("%i" % sender.get())
			self.updateView()

	def loadScrawl(self):
		if self.current_layer is None:
			return

		self.pen_size = self.current_layer.userData["%s.size" % plugin_id]
		if self.pen_size is None:
			self.pen_size = default_pen_size # scrawl pixels

		self.pixel_size = self.current_layer.userData["%s.unit" % plugin_id]
		if self.pixel_size is None:
			self.pixel_size = default_pixel_size # font units

		data = self.current_layer.userData["%s.data" % plugin_id]
		if data is None:
			self.data = initImage(self.current_layer, default_pixel_size)
		else:
			try:
				self.data = NSBitmapImageRep.alloc().initWithData_(data)
				self.data.setProperty_withValue_(NSImageColorSyncProfileData, None)
			except:
				self.data = initImage(self.current_layer, default_pixel_size)
		self.needs_save = False

	def saveScrawl(self):
		if self.current_layer is None:
			return
		self.current_layer.userData["%s.size" % plugin_id] = int(round(self.pen_size))
		self.current_layer.userData["%s.unit" % plugin_id] = int(round(self.pixel_size))
		if self.data is None:
			del self.current_layer.userData["%s.data" % plugin_id]
		else:
			imgdata = self.data.representationUsingType_properties_(NSPNGFileType, None)
			print("Saving PNG with %i bytes ..." % len(imgdata))
			if len(imgdata) > 2**16:
				print("Glyphs Bug: Image is too big to save")
				#imgdata.writeToFile_atomically_(join(dirname(__file__), "test.png"), False)
			else:
				self.current_layer.userData["%s.data" % plugin_id] = imgdata
		self.needs_save = False

	def deleteScrawl(self):
		if self.current_layer is None:
			return
		for key in ("unit", "data", "size"):
			full_key = "%s.%s" % (plugin_id, key)
			if self.current_layer.userData[full_key] is not None:
				del self.current_layer.userData[full_key]
		self.needs_save = False

	def saveScrawlToBackground(self):
		self.data = self.current_layer.userData["%s.data" % plugin_id]
		font = self.current_layer.parent.parent
		try:
			master = font.masters[self.current_layer.layerId]
		except KeyError:
			return
		if master is None:
			return
		pad = int(round(font.upm / 10))
		if self.data is not None:
			try:
				data = NSImage.alloc().initWithData_(self.data)
			except:
				return
			#self.current_layer.backgroundImage = GSBackgroundImage('/path/to/file.jpg')
			#self.current_layer.backgroundImage.position = NSPoint(-pad, master.descender - pad)
			#self.current_layer.backgroundImage.scale = (2 * pad + font.upm) / self.current_layer.backgroundImage.size().height
