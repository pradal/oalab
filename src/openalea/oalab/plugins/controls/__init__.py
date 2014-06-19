# -*- python -*-
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2014 INRIA
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


################################################################################
# Manual definition of Qt control widgets from openalea node widgets
################################################################################

from openalea.oalab.plugins.control import ControlWidgetSelectorPlugin
from openalea.deploy.shared_data import shared_data
import openalea.oalab
"""
class PluginIntSpinBox(ControlWidgetSelectorPlugin):

    controls = ['IInt']
    name = 'IntSpinBox'
    required = ['IInt.min', 'IInt.max']
    edit_shape = ['line', 'small']

    @classmethod
    def load(cls):
        from openalea.oalab.gui.control.widgets import IntSpinBox
        return IntSpinBox

class PluginIntSlider(ControlWidgetSelectorPlugin):

    controls = ['IInt']
    name = 'IntSlider'
    required = ['IInt.min', 'IInt.max']
    edit_shape = ['line', 'small']

    @classmethod
    def load(cls):
        from openalea.oalab.gui.control.widgets import IntSlider
        return IntSlider
"""

class PluginIntWidgetSelector(ControlWidgetSelectorPlugin):

    controls = ['IInt']
    name = 'IntWidgetSelector'
    required = ['IInt.min', 'IInt.max']
    edit_shape = ['responsive']
    icon_path = shared_data(openalea.oalab, 'icons/IntWidgetSelector_hline.png')

    @classmethod
    def load(cls):
        from openalea.oalab.plugins.controls.selectors import IntWidgetSelector
        return IntWidgetSelector


class PluginBoolWidgetSelector(ControlWidgetSelectorPlugin):

    controls = ['IBool']
    name = 'BoolWidgetSelector'
    edit_shape = ['responsive']

    @classmethod
    def load(cls):
        from openalea.oalab.plugins.controls.widgets import BoolCheckBox
        return BoolCheckBox


PluginOpenAleaLabWidgetSelectors = [
    PluginBoolWidgetSelector,
    PluginIntWidgetSelector
]

################################################################################
# Dynamic generation of Qt control widgets from openalea node widgets
################################################################################

PluginVisualeaWidgetSelectors = []

import openalea.visualea.gui_catalog
from openalea.core.interface import InterfaceWidgetMap
from openalea.vpltk.qt import QtCore, QtGui
from openalea.oalab.gui.control.widget import AbstractQtControlWidget
from openalea.oalab.plugins.controls.visualea_widgets import OpenAleaControlWidget


def OpenAleaControlWidgetFactory(OpenAleaControlWidget, OpenAleaWidget, interface):
    def __init__(self, **kwargs):
        OpenAleaControlWidget.__init__(self)
        OpenAleaWidget.__init__(self, None, None, None, interface)
        self.setAutoFillBackground(True)
        try:
            self.label.hide()
        except AttributeError:
            pass

    name = OpenAleaWidget.__name__ + 'Control'
    bases = [OpenAleaControlWidget, OpenAleaWidget]

    klass = type(name, tuple(bases), {'__init__':__init__})
    return klass

def new_plugin(widget_class, interface, shape=None):
    if shape is None :
        shape = ['large', 'hline']

    @classmethod
    def load(cls):
        return OpenAleaControlWidgetFactory(OpenAleaControlWidget, widget_class, interface())

    name = 'PluginOpenAlea%s' % interface.__name__
    klass = type(name, (ControlWidgetSelectorPlugin,), dict(load=load))
    klass.controls = [interface.__name__]
    klass.name = interface.__name__[1:] + 'Widget'
    klass.edit_shape = shape

    return klass

shapes = {
    'ISequence':['large'],
    'IFloat':None,
    'IDateTime':None,
}
for interface, widget_class in InterfaceWidgetMap().items():
    iname = interface.__name__
    if iname  in shapes:
        shape = shapes[iname]
        plugin = new_plugin(widget_class, interface, shape=shape)
        PluginVisualeaWidgetSelectors.append(plugin)

