
from openalea.oalab.applets.plugin import PluginApplet

class EditorManager(PluginApplet):

    name = 'EditorManager'
    alias = 'EditorManager'

    def __call__(self, mainwindow):
        # Load and instantiate graphical component that actually provide feature
        from openalea.oalab.applets.container import AppletContainer

        self._applet = AppletContainer(mainwindow.session, mainwindow)
        self._fill_menu(mainwindow, self._applet)

        mainwindow.add_applet(self._applet, self.alias, area='central')
