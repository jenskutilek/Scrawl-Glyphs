from __future__ import annotations

import objc
from GlyphsApp import Glyphs
from GlyphsApp.plugins import ReporterPlugin


from AppKit import NSClassFromString, NSCompositeSourceOver, \
    NSGraphicsContext, NSImage, NSImageInterpolationNone, NSMakeRect, \
    NSZeroRect


plugin_id = "de.kutilek.scrawl"


class ScrawlReporter(ReporterPlugin):

    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize({'en': u'Scrawl'})

    @objc.python_method
    def background(self, layer):

        # Check if the drawing should be shown

        currentController = self.controller.view().window().windowController()
        if currentController:
            tool = currentController.toolDrawDelegate()
            if tool.isKindOfClass_(NSClassFromString("GlyphsToolText")) \
                    or tool.isKindOfClass_(NSClassFromString("GlyphsToolHand")) \
                    or tool.isKindOfClass_(NSClassFromString("ScrawlTool")):
                return

        # draw pixels

        data = layer.userData["%s.data" % plugin_id]
        if data is None:
            return
        try:
            data = NSImage.alloc().initWithData_(data)
        except:
            print("Error in image data of layer %s" % layer)
            return

        rect = layer.userData["%s.rect" % plugin_id]
        if rect is None:
            # The drawing rect was not stored in user data.
            # Deduce it from the layer/font metrics.
            font = layer.parent.parent
            pad = int(round(font.upm / 10))

            # find master for image positioning (descender)

            try:
                descender = layer.parent.parent.masters[layer.layerId].descender
            except KeyError:
                descender = int(round(font.upm / 5))

            rect = NSMakeRect(
                -pad,
                descender - pad,
                2 * pad + layer.width,
                2 * pad + font.upm
            )
        else:
            # Use the rect from user data
            rect = NSMakeRect(*rect)
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.currentContext().setImageInterpolation_(
            NSImageInterpolationNone
        )
        if len(layer.paths) == 0:
            data.drawInRect_(rect)
        else:
            data.drawInRect_fromRect_operation_fraction_(
                rect,
                NSZeroRect,
                NSCompositeSourceOver,
                0.2
            )
        NSGraphicsContext.restoreGraphicsState()
