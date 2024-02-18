from __future__ import annotations

import objc
from GlyphsApp import Glyphs
from GlyphsApp.plugins import ReporterPlugin

from AppKit import NSClassFromString, NSCompositeSourceOver, \
    NSGraphicsContext, NSImage, NSImageInterpolationNone, NSMakeRect, \
    NSZeroRect


plugin_id = "de.kutilek.scrawl"
SCRAWL_DATA_KEY = f"{plugin_id}.data"
SCRAWL_RECT_KEY = f"{plugin_id}.rect"


class ScrawlReporter(ReporterPlugin):

    @objc.python_method
    def settings(self) -> None:
        self.menuName = Glyphs.localize({"en": "Scrawl"})

    @objc.python_method
    def background(self, layer) -> None:
        # Always show the drawing in the current layer background, except in certain
        # tools
        if self.controller is None:
            return

        currentController = self.controller.view().window().windowController()
        if currentController:
            tool = currentController.toolDrawDelegate()
            if tool.isKindOfClass_(NSClassFromString("GlyphsToolText")) \
                    or tool.isKindOfClass_(NSClassFromString("GlyphsToolHand")) \
                    or tool.isKindOfClass_(NSClassFromString("ScrawlTool")):
                return

        self.draw_layer(layer)

    @objc.python_method
    def preview(self, layer) -> None:
        # In preview, show only if the layer has neither components nor paths
        if layer.shapes:
            return

        self.draw_layer(layer)

    @objc.python_method
    def draw_layer(self, layer) -> None:
        # draw pixels

        data = layer.userData[SCRAWL_DATA_KEY]
        if data is None:
            return
        try:
            data = NSImage.alloc().initWithData_(data)
        except:  # noqa: 722
            print("Error in image data of layer %s" % layer)
            return

        rect = layer.userData[SCRAWL_RECT_KEY]
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
