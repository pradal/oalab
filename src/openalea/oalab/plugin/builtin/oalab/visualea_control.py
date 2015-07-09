# -*- coding: utf-8 -*-
# -*- python -*-
#
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2015 INRIA - CIRAD - INRA
#
#       File author(s): Guillaume Baty <guillaume.baty@inria.fr>
#
#       File contributor(s):
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################

from openalea.oalab.plugin.oalab.control import ControlWidgetSelectorPlugin
from openalea.core.plugin import PluginDef

################################################################################
# Dynamic generation of Qt control widgets from openalea node widgets
################################################################################

PluginVisualeaWidgetSelectors = []

import openalea.visualea.gui_catalog
from openalea.core.interface import InterfaceWidgetMap
from openalea.vpltk.qt import QtCore, QtGui
from openalea.oalab.control.widget import AbstractQtControlWidget, OpenAleaControlWidget


def OpenAleaControlWidgetFactory(OpenAleaControlWidget, OpenAleaWidget, interface):
    def __init__(self, **kwargs):
        OpenAleaControlWidget.__init__(self)
        OpenAleaWidget.__init__(self, None, None, None, interface)
        # self.setAutoFillBackground(True)
        try:
            self.label.hide()
        except AttributeError:
            pass

    name = OpenAleaWidget.__name__ + 'AutoGeneratedControl'
    bases = [OpenAleaControlWidget, OpenAleaWidget]

    klass = type(name, tuple(bases), {'__init__': __init__})
    return klass


def new_plugin(widget_class, interface, shape=None):
    if shape is None:
        shape = ['large', 'hline']

    def __call__(self):
        return OpenAleaControlWidgetFactory(OpenAleaControlWidget, widget_class, interface())

    name = 'PluginOpenAlea%s' % interface.__name__
    klass = type(name, (ControlWidgetSelectorPlugin,), dict(__call__=__call__))
    klass.controls = [interface.__name__]
    klass.name = interface.__name__[1:] + 'Widget'
    klass.edit_shape = shape
    klass.implements = ['IWidgetSelector']

    return PluginDef(klass)

DEFAULT_SHAPES = ['large', 'hline']
shapes = {
    'ISequence': ['large'],
    'IFloat': DEFAULT_SHAPES,
    'IDateTime': DEFAULT_SHAPES,
    'ITuple': DEFAULT_SHAPES,
    'IColor': DEFAULT_SHAPES,
    'ITextStr': DEFAULT_SHAPES,
    'IRGBColor': DEFAULT_SHAPES,
    'IInt': DEFAULT_SHAPES,
    'ICodeStr': ['large'],
    'IStr': DEFAULT_SHAPES,
    'IColor': DEFAULT_SHAPES,
    'IDict': DEFAULT_SHAPES,
    'IEnumStr': DEFAULT_SHAPES,
    'IColor': DEFAULT_SHAPES,
    'IFileStr': DEFAULT_SHAPES,
    'IDirStr': DEFAULT_SHAPES,
    'IBool': DEFAULT_SHAPES,
}

# Exclude interfaces that have widgets designed for controls
rejected = ['IInt', 'IStr', 'IFloat']

for interface, widget_class in InterfaceWidgetMap().items():
    iname = interface.__name__
    if iname in rejected:
        continue
    if iname in shapes:
        shape = shapes[iname]
    else:
        shape = None

    plugin = new_plugin(widget_class, interface, shape=shape)

    PluginVisualeaWidgetSelectors.append(plugin)
