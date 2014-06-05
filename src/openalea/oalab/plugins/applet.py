"""
===========================
Applet plugin documentation
===========================

To define an applet plugin, you must
  #. write an AppletPlugin class that respects IPluginApplet interface (see below)
  #. add it to group "oalab.applet"

1. Copy paste this code and fill it with right names and instructions.
(replace all xyz, respecting case, with your applet name).
For example Xyz -> HelpApplet


.. code-block :: python

    class PluginXyz(object):

        name = 'Xyz'
        alias = 'Xyz'

        def __call__(self, mainwindow):
            # Write your code here

        def instance(self):
            # Write your code here


To avoid to rewrite all plugins from scratch, you can derivate your plugin from
:class:`~openalea.oalab.plugins.applets.PluginApplet` :

.. code-block :: python

    from openalea.oalab.plugins.applets import PluginApplet
    class PluginXyz(PluginApplet):
        pass

2. Once this class has been written, just register it in the setup.py file of
your python package.

.. code-block :: python

    entry_points={
        'oalab.applet': [
            'Xyz = mypackage.plugins:PluginXyz',
            ]
        }


With **mypackage.plugins** python module path (equivalent to 'mypackage/plugins.py') and
'PluginXyz' the class name.


Details
=======

.. autoclass:: openalea.oalab.plugins.applet.IPluginApplet
    :members: __call__, instance, name, alias

.. autoclass:: openalea.oalab.plugins.applets.PluginApplet
    :members: __call__, instance, _fill_menu

"""
from openalea.core.interface import IInterface

class IApplet(IInterface):
    """
    Autonomous Graphical component
    """
    def initialize(self):
        """
        Optional method, called after instantiation
        """

class IPluginApplet(object):
    """
    Graphical component displayed in main window.
    Component must respect :class:`~openalea.oalab.plugins.applet.IApplet` interface.
    """

    name = 'AppletName'
    alias = 'Applet alias'

    def __call__(self, mainwindow):
        """
        Load and instantiate graphical component that actually provide feature.
        Then, place it in mainwindow (QMainWindow).


        Example:

        .. code-block :: python

            from mypackage import MyApplet

            self._applet = MyApplet()
            if self._applet.actions():
                for action in self._applet.actions():
                    # Add actions in PanedMenu
                    mainwindow.menu.addBtnByAction(*action)

                    # add action in classical menu
                    pane_name, group_name, act, btn_type = action
                    mainwindow.add_action_to_existing_menu(action=act, menu_name=pane_name, sub_menu_name=group_name)

            mainwindow.add_applet(self._applet, self.alias, area='inputs')

        """

    def instance(self):
        """
        returns widget instance if plugin has been called, else None.

        .. code-block :: python

            return self._applet

        """


