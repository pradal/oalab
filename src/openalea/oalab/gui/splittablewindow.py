# -*- coding: utf-8 -*-
# -*- python -*-
#
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2014 INRIA - CIRAD - INRA
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


import weakref
from openalea.vpltk.qt import QtGui, QtCore
from openalea.oalab.service.applet import new_applet
from openalea.oalab.gui.splitterui import SplittableUI, BinaryTree
from openalea.core.service.plugin import (new_plugin_instance, plugin_instances, plugin_class,
                                          plugins, plugin_instance, plugin_instance_exists)
from openalea.oalab.gui.utils import qicon
from openalea.oalab.gui.menu import ContextualMenu
from openalea.core.plugin.manager import PluginManager

import openalea.core


def menu_actions(widget):
    actions = []
    if widget is None:
        return actions
    if hasattr(widget, 'menu_actions'):
        actions += widget.menu_actions()
    elif widget.actions():
        actions += widget.actions()
    return actions


def fill_menu(menu, actions):
    for action in actions:
        if isinstance(action, QtGui.QAction):
            menu.addAction(action)
        elif isinstance(action, (list, tuple)):
            menu.addAction(action[2])
        elif isinstance(action, QtGui.QMenu):
            menu.addMenu(action)
        elif action == '-':
            menu.addSeparator()
        else:
            continue


def fill_panedmenu(menu, actions):
    for action in actions:
        if isinstance(action, QtGui.QAction):
            menu.addBtnByAction('Default', 'Default', action, 0)
        elif isinstance(action, (list, tuple)):
            menu.addBtnByAction(*action)
        elif isinstance(action, dict):
            args = [
                action.get('pane', 'Default'),
                action.get('group', 'Default'),
                action['action'],
                action.get('style', 0)
            ]
            menu.addBtnByAction(*args)
        elif isinstance(action, QtGui.QMenu):
            pass
        else:
            continue


def obj_icon(obj, rotation=0, size=(64, 64)):
    if hasattr(obj, 'icon'):
        icon = qicon(obj.icon)
    else:
        icon = qicon('oxygen_application-x-desktop.png')

    if rotation:
        pix = icon.pixmap(*size)
        transform = QtGui.QTransform()
        transform.rotate(rotation)
        pix = pix.transformed(transform)
        icon = QtGui.QIcon(pix)
    return icon


class AppletSelector(QtGui.QWidget):

    """
    Combobox listing all applets available.
    Signals:
      - appletChanged(name): sent when an applet is selected 
    """

    appletChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setContentsMargins(0, 0, 0, 0)
        self._layout = QtGui.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._cb_applets = QtGui.QComboBox()
        self._applet_plugins = []

        self._cb_applets.addItem('Select applet')
        for plugin_class in plugins('oalab.applet'):
            self._applet_plugins.append(plugin_class)
            self._cb_applets.addItem(obj_icon(plugin_class), plugin_class.alias)

        self._layout.addWidget(self._cb_applets)

        self.setCurrentApplet('')
        self._cb_applets.currentIndexChanged.connect(self._on_current_applet_changed)

    def _on_current_applet_changed(self, idx):
        """
        Called when selected applet changes.
        Emit signal appletChanged(name)
        name = '' if applet not found or "select applet"
        """
        applet_name = self.applet(idx)
        if applet_name:
            self.appletChanged.emit(applet_name)
        else:
            self.appletChanged.emit('')

    def applet(self, idx):
        if 1 <= idx <= len(self._applet_plugins):
            plugin_class = self._applet_plugins[idx - 1]
            return plugin_class.name
        else:
            return None

    def currentAppletName(self):
        return self.applet(self._cb_applets.currentIndex())

    def setCurrentApplet(self, name):
        self._cb_applets.setCurrentIndex(0)
        for i, plugin_class in enumerate(self._applet_plugins):
            if plugin_class.name == name:
                self._cb_applets.setCurrentIndex(i + 1)
                break


class AppletFrame(QtGui.QWidget):

    """
    """

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self._show_toolbar = False
        self._show_title = False
        self._edit_mode = False

        self._applet = None

        self.setContentsMargins(0, 0, 0, 0)
        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._l_title = QtGui.QLabel('No applet selected')
        self._l_title.hide()
        self._menu = ContextualMenu()

        p = QtGui.QSizePolicy
        self._l_title.setSizePolicy(p(p.MinimumExpanding, p.Maximum))
        self._l_title.setAlignment(QtCore.Qt.AlignVCenter)

        self._layout.setAlignment(self._l_title, QtCore.Qt.AlignVCenter)

        self._layout.addWidget(self._l_title)
        self._layout.addWidget(self._menu)

        self._create_actions()

    def _create_actions(self):
        self.action_toolbar = QtGui.QAction("Toolbar", self)
        self.action_toolbar.setCheckable(True)
        self.action_toolbar.toggled.connect(self.show_toolbar)

        self.action_title = QtGui.QAction("Show Tab Title", self)
        self.action_title.setCheckable(True)
        self.action_title.toggled.connect(self.show_title)

    def menu_actions(self):
        if self._applet:
            applet = self._applet()
        else:
            applet = None
        if self._edit_mode:
            actions = [self.action_title, self.action_toolbar]
        else:
            actions = menu_actions(applet)
        return actions

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu()
        fill_menu(menu, self.menu_actions())
        menu.exec_(event.globalPos())

    def set_edit_mode(self, edit=True):
        self._edit_mode = edit

    def set_applet(self, applet):
        self._applet = weakref.ref(applet)
        self._layout.insertWidget(1, applet)
        _plugin_class = plugin_class('oalab.applet', applet.name)
        self._l_title.setText(_plugin_class.alias)
        p = QtGui.QSizePolicy
        applet.setSizePolicy(p(p.MinimumExpanding, p.MinimumExpanding))

    def remove_applet(self, applet):
        self._layout.removeWidget(applet)

    def show_title(self, show=True):
        self._show_title = show
        self.action_title.setChecked(show)
        self._l_title.setVisible(show)

    def show_toolbar(self, show=True):
        self._show_toolbar = show
        self.action_toolbar.setChecked(show)
        if show:
            self.fill_toolbar()
        else:
            self.clear_toolbar()

    def fill_toolbar(self):

        if self._show_toolbar is False:
            return

        if self._applet is None:
            return

        applet = self._applet()
        if applet is None:
            return

        # Fill toolbar
        self._menu.show()
        self.clear_toolbar()
        try:
            actions = applet.toolbar_actions()
        except AttributeError:
            pass
        else:
            fill_panedmenu(self._menu, actions)

    def clear_toolbar(self):
        if self._show_toolbar:
            self._menu.clear()
        else:
            self._menu.hide()

    def properties(self):
        return dict(
            toolbar=self._show_toolbar,
            title=self._show_title
        )

    def set_properties(self, properties):
        get = properties.get
        self.show_toolbar(get('toolbar', False))
        self.show_title(get('title', False))


class AppletTabWidget(QtGui.QTabWidget):
    appletSet = QtCore.Signal(object, object)

    def __init__(self):
        QtGui.QTabWidget.__init__(self)

        # Display options
        self.setContentsMargins(0, 0, 0, 0)
        self.setDocumentMode(True)

        # Tab management
        self.setMovable(True)
        self.tabCloseRequested.connect(self.remove_tab)
        self.tabBar().tabMoved.connect(self._on_tab_moved)

        # Internal dicts
        # dict: idx -> name -> applet.
        # Ex: self._applets[0]['Help'] -> <HelpWidget instance at 0x7fea19a07d88>
        self._applets = {}

        # dict: idx -> name of current applet
        self._name = {}

        # Set in edit mode by default
        self.set_edit_mode()

    def tabInserted(self, index):
        self.tabBar().setVisible(self.count() > 1)

    def tabRemoved(self, index):
        self.tabBar().setVisible(self.count() > 1)

    def setTabPosition(self, *args, **kwargs):
        rvalue = QtGui.QTabWidget.setTabPosition(self, *args, **kwargs)
        for idx in range(self.count()):
            self._redraw_tab(idx)
        return rvalue

    def _on_tab_moved(self, old, new):
        self._name[old], self._name[new] = self._name[new], self._name[old]
        self._applets[old], self._applets[new] = self._applets[new], self._applets[old]
        self._redraw_tab(old)
        self._redraw_tab(new)

    def set_edit_mode(self, mode=True):
        self._edit_mode = mode
        applet_frame = self.currentWidget()
        if applet_frame:
            applet_frame.set_edit_mode(mode)
        self.setTabsClosable(mode)

    def menu_actions(self):
        return menu_actions(self.currentWidget())

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu()
        fill_menu(menu, self.menu_actions())
        menu.exec_(event.globalPos())

    def new_tab(self):
        widget = AppletFrame()
        widget.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.addTab(widget, '')
        self.setCurrentWidget(widget)

    def remove_tab(self, idx):
        """
         - Destroy all applets in current tabs (current applet and previous hidden applets)
         - Then, remove tab.
        """
        if idx in self._applets:
            tab = self.currentWidget()
            for applet in self._applets[idx].values():
                tab.remove_applet(applet)
                applet.close()
                del applet
            del self._applets[idx]
            del self._name[idx]
        self.removeTab(idx)

    def set_applet(self, name, properties=None):
        """
        Show applet "name" in current tab.
        """
        # clear view (hide all widgets in current tab)
        idx = self.currentIndex()
        old = self._name.get(idx, None)
        for applet in self._applets.get(idx, {}).values():
            applet.hide()

        if not name:
            return

        # If applet has been instantiated before, just show it
        # Else, instantiate a new one, place it in layout and show it
        if name in self._applets.get(idx, {}):
            applet = self._applets[idx][name]
            applet.show()
        else:
            # If applet has never been instantiated in the whole application,
            # we instantiate it as the "main" instance (ie reachable thanks to plugin_instance)
            # else, just create a new one.
            if plugin_instance_exists('oalab.applet', name):
                applet = new_plugin_instance('oalab.applet', name)
            else:
                applet = plugin_instance('oalab.applet', name)

            if applet is None:
                return

            applet.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            applet.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
            applet.name = name
            if properties:
                try:
                    applet.set_properties(properties)
                except AttributeError:
                    pass

            tab = self.currentWidget()
            tab.set_applet(applet)
            self._applets.setdefault(idx, {})[name] = applet

        self._name[idx] = name
        self._redraw_tab(idx)

        self.appletSet.emit(old, name)

    def _redraw_tab(self, idx):
        """
        """
        if idx not in self._name:
            return

        name = self._name[idx]
        _plugin_class = plugin_class('oalab.applet', name)
        #self.setTabText(idx, _plugin_class.alias)
        if self.tabPosition() == QtGui.QTabWidget.East:
            rotation = -90
        elif self.tabPosition() == QtGui.QTabWidget.West:
            rotation = 90
        else:
            rotation = 0

        self.setTabIcon(idx, obj_icon(_plugin_class, rotation=rotation))
        self.setTabToolTip(idx, _plugin_class.alias)
        self.widget(idx).set_edit_mode(self._edit_mode)

    def currentAppletName(self):
        try:
            return self._name[self.currentIndex()]
        except KeyError:
            return None

    def currentApplet(self):
        try:
            name = self.currentAppletName()
            return self._applets[self.currentIndex()][name]
        except KeyError:
            return None

    def properties(self):
        return dict(position=self.tabPosition())

    def set_properties(self, properties):
        get = properties.get
        self.setTabPosition(get('position', 0))

    def _repr_json_(self):
        applets = []
        for idx in range(self.count()):
            if idx in self._name:
                name = self._name[idx]
                properties = self.currentWidget().properties()
                try:
                    properties.update(self._applets[idx][name].properties())
                except AttributeError:
                    pass
                applets.append(dict(name=name, properties=properties))
        layout = dict(applets=applets, properties=self.properties())
        return layout


class AppletContainer(QtGui.QWidget):
    appletSet = QtCore.Signal(object, object)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, None)

        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

        self._applets = []
        self._edit_mode = True

        self._e_title = QtGui.QLabel('')
        self._e_title.hide()

        self._tabwidget = AppletTabWidget()
        self._tabwidget.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self._tabwidget.appletSet.connect(self.appletSet.emit)
        self._tabwidget.currentChanged.connect(self._on_tab_changed)
        self.appletSet.connect(self._on_applet_changed)

        self._applet_selector = AppletSelector()
        self._applet_selector.appletChanged.connect(self._tabwidget.set_applet)

        self._layout.addWidget(self._e_title)
        self._layout.addWidget(self._tabwidget)
        self._layout.addWidget(self._applet_selector)

        self._tabwidget.new_tab()

        applet_name = self._applet_selector.currentAppletName()
        if applet_name:
            self._tabwidget.set_applet(applet_name)

        self._create_menus()
        self._create_actions()
        self._fill_menus()

        self.set_edit_mode()

    def _create_actions(self):
        self.action_title = QtGui.QAction("Set Title", self)
        self.action_title.triggered.connect(self._on_set_title_triggered)

        self.action_unlock = QtGui.QAction(qicon('oxygen_object-unlocked.png'), "Edit layout", self.menu_edit_off)
        self.action_unlock.triggered.connect(self.unlock_layout)

        self.action_lock = QtGui.QAction(qicon('oxygen_object-locked.png'), "Lock layout", self.menu_edit_on)
        self.action_lock.triggered.connect(self.lock_layout)

        self.action_add_tab = QtGui.QAction(qicon('Crystal_Clear_action_edit_add.png'), "Add tab", self.menu_edit_on)
        self.action_add_tab.triggered.connect(self._tabwidget.new_tab)

        self.action_remove_tab = QtGui.QAction(
            qicon('Crystal_Clear_action_edit_remove.png'), "Remove tab", self.menu_edit_on)
        self.action_remove_tab.triggered.connect(self._tabwidget.remove_tab)

    def _create_menus(self):
        # Menu if edit mode is OFF
        self.menu_edit_off = QtGui.QMenu(self)
        self.menu_edit_on = QtGui.QMenu(self)

    def _fill_menus(self):
        self.menu_edit_off.addAction(self.action_unlock)
        self.menu_edit_off.addSeparator()

        # Menu if edit mode is ON

        self.menu_edit_on.addAction(self.action_lock)
        self.menu_edit_on.addSeparator()
        self.menu_edit_on.addAction(self.action_add_tab)
        self.menu_edit_on.addAction(self.action_remove_tab)
        self.menu_edit_on.addSeparator()
        self.menu_edit_on.addAction(self.action_title)

        self._position_actions = {}
        for name, position in [
                ('top', QtGui.QTabWidget.North),
                ('right', QtGui.QTabWidget.East),
                ('bottom', QtGui.QTabWidget.South),
                ('left', QtGui.QTabWidget.West)]:
            action = QtGui.QAction("Move tab to %s" % name, self.menu_edit_on)
            action.triggered.connect(self._on_tab_position_changed)
            self.menu_edit_on.addAction(action)
            self._position_actions[action] = position

    def menu_actions(self):
        if self._edit_mode is True:
            actions = self.menu_edit_on.actions()
            actions += self._tabwidget.menu_actions()
        else:
            actions = self.menu_edit_off.actions()
            actions += self._tabwidget.menu_actions()
        return actions

    def emit_applet_set(self):
        for applet in self._applets:
            self.appletSet.emit(None, applet)

    def add_applets(self, applets, **kwds):
        """
        applets: list of dict defining applets.
        Each dict must define at least a key "name".
        Ex: applets = [{'name':'MyWidget'}]
        """
        names = []
        for i, applet in enumerate(applets):
            name = applet['name']
            names.append(name)
            properties = applet.get('properties', {})
            if i:
                self._tabwidget.new_tab()
            self._tabwidget.set_applet(name, properties=properties)
            self._tabwidget.currentWidget().set_properties(properties)
        self._tabwidget.setCurrentIndex(0)
        self._applets = names

    def _on_tab_position_changed(self):
        self._tabwidget.setTabPosition(self._position_actions[self.sender()])

    def _on_tab_changed(self, idx):
        applet_name = self._tabwidget.currentAppletName()
        if applet_name:
            self._applet_selector.setCurrentApplet(applet_name)

    def _on_applet_changed(self, old, new):
        pass

    def lock_layout(self):
        self.set_edit_mode(False)

    def unlock_layout(self):
        self.set_edit_mode(True)

    def set_edit_mode(self, mode=True):
        self._applet_selector.setVisible(mode)
        self._edit_mode = mode
        self._tabwidget.set_edit_mode(mode)

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu()
        fill_menu(menu, self.menu_actions())
        menu.exec_(event.globalPos())

    def properties(self):
        properties = {}
        properties.update(self._tabwidget.properties())
        title = unicode(self._e_title.text()).strip()
        if title:
            properties['title'] = title
        return properties

    def set_properties(self, properties):
        self._tabwidget.set_properties(properties)
        self.set_title(properties.get('title', None))

    def _on_set_title_triggered(self):
        from openalea.oalab.service.qt_control import qt_dialog
        value = qt_dialog(name='Title', interface='IStr', value=self._e_title.text())
        if value is not None:
            self.set_title(value)

    def set_title(self, title):
        if title:
            self._e_title.show()
            self._e_title.setText(title)
        else:
            self._e_title.hide()
            self._e_title.setText('')

    def toString(self):
        json = self._tabwidget._repr_json_()
        json.setdefault('properties', {}).update(self.properties())
        return json


class OABinaryTree(BinaryTree):

    def toString(self, props=[]):
        filteredProps = {}
        for vid, di in self._properties.iteritems():
            filteredProps[vid] = {}
            for k, v in di.iteritems():
                if k in props:
                    if hasattr(v, 'toString'):
                        filteredProps[vid][k] = v.toString()
                    else:
                        filteredProps[vid][k] = v
        return repr(self._toChildren) + ", " + repr(self._toParents) + ", " + repr(filteredProps)


class InitContainerVisitor(object):

    """Visitor that searches which leaf id has pos in geometry"""

    def __init__(self, graph, wid):
        self.g = graph
        self.wid = wid

    def _to_qwidget(self, widget):
        if isinstance(widget, dict):
            properties = widget.get('properties', {})
            applets = widget.get('applets', [])
            if applets is None:
                return widget
            container = AppletContainer()
            container.add_applets(applets)
            container.set_properties(properties)
            widget = container
        return widget

    def visit(self, vid):
        """
        """
        if self.g.has_property(vid, 'widget'):
            widget = self.g.get_property(vid, "widget")
            widget = self._to_qwidget(widget)
        else:
            widget = None

        if not self.g.has_children(vid):
            self.wid._install_child(vid, widget)
            widget.emit_applet_set()
            return False, False

        direction = self.g.get_property(vid, "splitDirection")
        amount = self.g.get_property(vid, "amount")
        self.wid._split_parent(vid, direction, amount)

        return False, False


class OALabSplittableUi(SplittableUI):

    reprProps = ["amount", "splitDirection", "widget"]
    appletSet = QtCore.Signal(object, object)

    def __init__(self, parent=None, content=None):
        """Contruct a SplittableUI.
        :Parameters:
         - parent (qt.QtGui.QWidget)  - The parent widget
         - content (qt.QtGui.QWidget) - The widget to display in pane at level 0
        """
        QtGui.QWidget.__init__(self, parent)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setAcceptDrops(True)
        # -- our backbone: --
        self._g = OABinaryTree()
        # -- contains geometry information (a vid->QRect mapping) --
        self._geomCache = {}
        # -- initialising the pane at level 0 --
        self._geomCache[0] = self.contentsRect()
        self._install_child(0, content)

        self._containers = {}

        self.set_edit_mode()

    def _connect_container(self, container):
        if isinstance(container, AppletContainer):
            if container not in self._containers:
                container.appletSet.connect(self.appletSet.emit)
                self._containers[container] = container

    def getPlaceHolder(self):
        container = AppletContainer()
        self._connect_container(container)
        return container

    def setContentAt(self, paneId, wid, **kwargs):
        self._connect_container(wid)
        return SplittableUI.setContentAt(self, paneId, wid, **kwargs)

    def _install_child(self, paneId, widget, **kwargs):
        g = self._g
        self._connect_container(widget)

        # -- get the old content --
        oldWidget = None
        if g.has_property(paneId, "widget"):
            oldWidget = g.get_property(paneId, "widget")
            if isinstance(oldWidget, QtGui.QWidget):
                oldWidget.hide()

        # -- place the new content --
        if widget is not None:
            widget.setParent(self)
            widget.show()

        g.set_property(paneId, "widget", widget)

        if not kwargs.get("noTearOffs", False):
            self._install_tearOffs(paneId)
        return oldWidget

    @classmethod
    def FromString(cls, rep, parent=None):
        g, tup = OABinaryTree.fromString(rep)

        newWid = cls(parent=parent)
        w0 = newWid._uninstall_child(0)
        if w0:
            w0.setParent(None)
            w0.close()

        newWid._g = g
        visitor = InitContainerVisitor(g, newWid)
        g.visit_i_breadth_first(visitor)
        newWid._geomCache[0] = newWid.contentsRect()
        newWid.computeGeoms(0)
        return newWid

    def fromString(self, rep, parent=None):
        g, tup = OABinaryTree.fromString(rep)

        w0 = self._uninstall_child(0)
        if w0:
            w0.setParent(None)
            w0.close()

        self._g = g
        visitor = InitContainerVisitor(g, self)
        g.visit_i_breadth_first(visitor)
        self._geomCache[0] = self.contentsRect()
        self.computeGeoms(0)

    def _onSplitRequest(self, paneId, orientation, amount):
        if self._edit_mode:
            SplittableUI._onSplitRequest(self, paneId, orientation, amount)
        else:
            return

    def set_edit_mode(self, mode=True):
        self._edit_mode = mode
        for properties in self._g._properties.values():

            # if 'handleWidget' in properties:
            #    properties['handleWidget'].setVisible(mode)

            if 'tearOffWidgets' in properties:
                for widget in properties['tearOffWidgets']:
                    widget.set_edit_mode(mode)

            if 'widget' in properties:
                widget = properties['widget']
                if widget:
                    widget.set_edit_mode(mode)


class OALabMainWin(QtGui.QMainWindow):
    appletSet = QtCore.Signal(object, object)
    DEFAULT_MENU_NAMES = ('Project', 'Edit', 'View', 'Help')

    def __init__(self, layout=None):
        QtGui.QMainWindow.__init__(self)

        # Classic menu
        self.menu_classic = {}
        self._registered_applets = []
        menubar = QtGui.QMenuBar()

        for menu_name in self.DEFAULT_MENU_NAMES:
            self.menu_classic[menu_name] = menubar.addMenu(menu_name)

        self.setMenuBar(menubar)

        self.splittable = OALabSplittableUi(parent=self)
        self.splittable.appletSet.connect(self.appletSet.emit)
        self.appletSet.connect(self._on_applet_set)

        if layout is None:
            container = AppletContainer()
            self.splittable.setContentAt(0, container)
        else:
            self.splittable.fromString(str(layout))

        self.setCentralWidget(self.splittable)

        QtGui.QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def set_edit_mode(self, mode=True):
        for widget in self.splittable.getAllContents():
            if hasattr(widget, 'set_edit_mode'):
                widget.set_edit_mode(mode)
        self.splittable.set_edit_mode(mode)

    def initialize(self):
        self.pm = PluginManager()
        for instance in plugin_instances('oalab.applet'):
            if hasattr(instance, 'initialize'):
                instance.initialize()

    def _actions(self, obj):
        actions = None
        if hasattr(obj, 'toolbar_actions'):
            if isinstance(obj.toolbar_actions, list):
                actions = obj.toolbar_actions
            else:
                actions = obj.toolbar_actions()

        if actions is None:
            return []
        else:
            return actions

    def _on_focus_changed(self, old, new):
        if new is None:
            self.clear_toolbar()
            return

        if old is new:
            return

        # Generally focus is on "leaf" widget on widget hierarchy.
        # We try to browse all tree to get widget defining actions
        # For example, if an editor is defined as MyEditor -> Container -> Editor -> QTextEdit
        # Widget with focus is QTextEdit but widget that define actions is MyEditor
        # Search stops if widget has no more parents or if widget is AppletContainer
        parent = new
        actions = self._actions(parent)
        while parent is not None:
            try:
                parent = parent.parent()
            except TypeError:
                break
            else:
                if isinstance(parent, AppletContainer):
                    break
                actions += self._actions(parent)

        if actions:
            self.fill_toolbar(actions)
        else:
            self.clear_toolbar()
        # toolbar creation/destruction set focus to toolbar so we reset it to widget
        new.setFocus(QtCore.Qt.OtherFocusReason)

    def fill_toolbar(self, actions):
        menus = plugin_instances('oalab.applet', 'ContextualMenu')
        for menu in menus:
            menu.clear()
            fill_panedmenu(menu, actions)

    def clear_toolbar(self):
        menus = plugin_instances('oalab.applet', 'ContextualMenu')
        for menu in menus:
            menu.clear()

    def _merge_menus(self, menus):
        parent = self
        default_menus = self.menu_classic
        menubar = self.menuBar()

        for _menu in menus:
            menu_name = _menu.title()
            if menu_name in default_menus:
                menu = default_menus[menu_name]
            else:
                menu = QtGui.QMenu(menu_name, parent)
                default_menus[menu_name] = menu
                menubar.addMenu(menu)

        for _menu in menus:
            menu_name = _menu.title()
            menu = default_menus[menu_name]
            for action in _menu.actions():
                if isinstance(action, QtGui.QAction):
                    menu.addAction(action)
                elif isinstance(action, QtGui.QMenu):
                    menu.addMenu(action)
                elif action == '-':
                    menu.addSeparator()

    def _on_applet_set(self, old, new):
        if new in self._registered_applets:
            return

        self._registered_applets.append(new)
        applet = plugin_instance('oalab.applet', new)

        # Add global menus
        if applet and hasattr(applet, 'menus'):
            menus = applet.menus()
            if menus is None:
                return
            self._merge_menus(menus)

        # Add global toolbars
        if applet and hasattr(applet, 'toolbars'):
            toolbars = applet.toolbars()
            if toolbars is None:
                return
            for toolbar in toolbars:
                self.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

    def layout(self):
        return eval(self.splittable.toString())

from openalea.core.path import path as Path
from openalea.core.service.ipython import interpreter


class TestMainWin(OALabMainWin):
    DEFAULT_LAYOUT = ({}, {0: None}, {0: {
        'widget': {
            'properties': {'position': 0},
            'applets': [{'name': 'ShellWidget'}]
        }
    }})

    def __init__(self, layout=None, **kwds):
        """
        tests: list of function runnable in shell (name changed to run_<funcname>)
        layout_file
        """
        layout_file = kwds.pop('layout_file', 'layout.oaui')
        default_layout = kwds.pop('default_layout', self.DEFAULT_LAYOUT)

        self.layout_filepath = Path(layout_file).abspath()
        if layout is None:
            if self.layout_filepath.exists():
                with open(self.layout_filepath) as layout_file:
                    layout = eval(layout_file.read())

        if layout is None:
            layout = default_layout

        OALabMainWin.__init__(self, layout=layout)

        self.interp = interpreter()
        self.interp.user_ns['mainwin'] = self
        self.interp.user_ns['debug'] = self.debug

        from openalea.core.service.plugin import plugin_instance, plugin_instances

        def applet(name):
            return plugin_instance('oalab.applet', name)

        def applets(name):
            return plugin_instances('oalab.applet', name)

        self.interp.user_ns['applet'] = applet
        self.interp.user_ns['applets'] = applets

        for f in kwds.pop('tests', []):
            self.interp.user_ns['run_%s' % f.__name__] = f

        self.set_edit_mode()

    def closeEvent(self, event):
        with open(self.layout_filepath, 'w') as layout_file:
            layout_file.write(str(self.layout()))

    def debug(self):
        from openalea.oalab.session.session import Session
        session = Session()
        self.interp.user_ns['session'] = session
        session.debug = True
