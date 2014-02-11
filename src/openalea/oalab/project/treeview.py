# -*- python -*-
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2013 INRIA - CIRAD - INRA
#
#       File author(s): Julien Coste <julien.coste@inria.fr>
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

"""
Display a tree view of the project in oalab
"""

__revision__ = "$Id: "

from openalea.vpltk.qt import QtGui, QtCore
from openalea.core.path import path
from openalea.core import settings
import os

class ProjectLayoutWidget(QtGui.QWidget):
    """
    Widget to display the name of the current project AND the project
    """
    def __init__(self, session, controller, parent=None):
        super(ProjectLayoutWidget, self).__init__(parent=parent) 
        self.session = session
        self.treeview = ProjectTreeView(self.session, controller, parent)
        self.label = ProjectLabel(self.session, controller, parent)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.treeview)
        
        self.setLayout(layout)
        
    def clear(self):
        self.treeview.reinit_treeview()
        self.label.setText("")  
        
    def update(self):
        self.treeview.update()
        self.label.update()
        
    def mainMenu(self):
        """
        :return: Name of menu tab to automatically set current when current widget
        begin current.
        """
        return self.treeview.mainMenu()

class ProjectLabel(QtGui.QLabel):
    """
    Widget to display the name of the current project.
    """
    def __init__(self, session, controller, parent=None):
        super(ProjectLabel, self).__init__(parent=None) 
        self.session = session
        self.update()
        
    def update(self):    
        if self.session.current_is_project():
            label = self.session.project.name
        elif self.session.current_is_script():
            label = "Files"
        else:
            label = ""
        self.setText(label)  

class ProjectTreeView(QtGui.QTreeView):
    """
    Widget to display Tree View of project.
    """
    def __init__(self, session, controller, parent=None):
        super(ProjectTreeView, self).__init__(parent) 
        #self.setIconSize(QtCore.QSize(30,30))
        self.session = session
        self.controller = controller
        
        if self.session.current_is_project():
            self.project = self.session.project
        elif self.session.current_is_script():
            self.project = self.session.project
        else:
            self.project = None
            
        self.projectview = QtGui.QWidget()
        
        # project tree view
        self.proj_model = PrjctModel(session, controller, self.project)
        
        self.setHeaderHidden(True)
        self.setModel(self.proj_model)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        QtCore.QObject.connect(self,QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'),self.showMenu)
        
    def update(self):
        self.reinit_treeview()
        
    def reinit_treeview(self):
        """ Reinitialise project view """
        
        if self.session.current_is_project():
            self.project = self.session.project
        elif self.session.current_is_script():
            self.project = self.session.project
        else:
            self.project = None
        self.proj_model.set_proj(self.project)
        self.expandAll()
        
    def create_menu(self):
        menu = QtGui.QMenu(self)

        for applet in self.controller.applet_container.paradigms.values():
            action = QtGui.QAction('New %s Model'%applet.default_name,self)
            toconnect = "self.controller.project_manager.new%s"%applet.default_name
            action.triggered.connect(eval(toconnect))
            menu.addAction(action)
        menu.addSeparator()
        importAction = QtGui.QAction('Import Model',self)
        importAction.triggered.connect(self.controller.project_manager.importFile)
        menu.addAction(importAction)
        menu.addSeparator()
        renameAction = QtGui.QAction('Rename Project',self)
        renameAction.triggered.connect(self.controller.project_manager.renameCurrent)
        menu.addAction(renameAction)  
        
        return menu

    def showMenu(self, event):
        """ function defining actions to do according to the menu's button chosen"""
        menu = self.create_menu()
        menu.exec_(self.mapToGlobal(event))

    def hasSelection(self):
        """function hasSelection: check if an object is selected, return True in this case"""
        return self.selectionModel().hasSelection()
        
    def hasParent(self):
        if self.hasSelection():
            index = self.selectedIndexes()[0]
            item = index.model().itemFromIndex(index)
            parent = item.parent()
            return bool(parent)
        else:
            return False

    def mainMenu(self):
        """
        :return: Name of menu tab to automatically set current when current widget
        begin current.
        """
        return "Project"  


class PrjctModel(QtGui.QStandardItemModel):
    """
    Item model to use TreeView with a project.
    
    Use:
    
    # Project to display
    project = ...

    # Model to transform a project into a tree
    proj_model = PrjctModel(project)

    # Create tree view and set model
    treeView = QtGui.QTreeView()
    treeView.setModel(proj_model)
    
    # Display
    treeView.show()
    """
    def __init__(self, session, controller, project, parent=None):
        super(PrjctModel, self).__init__(parent)
        
        # Use it to store evrything to compare with new when a change occure
        self.controller = controller
        
        self.old_models = list()
        self.old_controls = list()
        self.old_scene = list()
        
        self.proj = None
        self.set_proj(project)      

        QtCore.QObject.connect(self,QtCore.SIGNAL('dataChanged( const QModelIndex &, const QModelIndex &)'),self.renamed)
        
        self.icons = dict()
        for applet in self.controller.applet_container.paradigms.values():
            self.icons[applet.extension] = applet.icon
        
    def renamed(self,x,y):
        if self.proj is not None:
            if self.proj.is_project():
                # Get item and his parent
                parent = self.item(x.parent().row())
                # Check if you have the right to rename
                if parent:
                    item = parent.child(x.row())
                
                    # List brothers of item
                    children = list()
                    raw = parent.rowCount()
                    for i in range(raw):
                        child = parent.child(i)
                        children.append(child.text())
                    
                    # Search which is the old_item which was changed and rename it
                    if parent.text() == "Models":
                        for i in self.old_models:
                            if i not in children:
                                self.proj.rename(categorie=parent.text(), old_name=i, new_name= item.text())

                    if parent.text() == "Controls":
                        for i in children:
                            if i not in self.old_controls:
                                self.proj.rename(categorie=parent.text(), old_name=i, new_name= item.text())

                    if parent.text() == "Scene":
                        for i in children:
                            if i not in self.old_scene:
                                self.proj.rename(categorie=parent.text(), old_name=i, new_name= item.text())
                                
                    # Save project
                    self.proj.save()
        

    def set_proj(self, proj=None):
        self.clear()
        
        if proj is not None:
            self.proj = proj
            self._set_level_0()
            self._set_level_1()

    def _set_level_0(self):
        ## TODO if you want to see all objects of the project
        
        if self.proj.is_project():
            #level0 = ["Models", "Controls", "Scene"]
            # TODO : add controls, scene, import, ...
            level0 = ["Models"]
                                
            for name in level0:
                parentItem = self.invisibleRootItem()
                item = QtGui.QStandardItem(name)
                if name == "Controls": icon = QtGui.QIcon(":/images/resources/node.png")
                elif name == "Scene": icon = QtGui.QIcon(":/images/resources/plant.png")
                elif name == "Models": icon = QtGui.QIcon(":/images/resources/package.png")
                item.setIcon(icon)
                parentItem.appendRow(item)

        elif self.proj.is_script():
            rootItem = self.invisibleRootItem()
            for name in self.proj:
                item = QtGui.QStandardItem(name)
                ext = name.split(".")[-1]
                if ext in self.icons.keys():
                    item.setIcon(QtGui.QIcon(self.icons[ext]))
                else:
                    item.setIcon(QtGui.QIcon(":/images/resources/openalea_icon2.png"))
                rootItem.appendRow(item)    

    def _set_level_1(self):
        if self.proj.is_project():
            self.old_models = list()
            self.old_controls = list()
            self.old_scene = list()
            
            rootItem = self.invisibleRootItem()
            
            # Controls
            parentItem = rootItem.child(1)
            for name in self.proj.controls:
                item = QtGui.QStandardItem(name)
                item.setIcon(QtGui.QIcon(":/images/resources/bool.png"))
                #parentItem.appendRow(item)    
                self.old_controls.append(name)
                 
            # Models
            parentItem = rootItem.child(0)
            for name in self.proj.scripts:
                item = QtGui.QStandardItem(name)
                ext = name.split(".")[-1]
                if ext in self.icons.keys():
                    item.setIcon(QtGui.QIcon(self.icons[ext]))
                else:
                    item.setIcon(QtGui.QIcon(":/images/resources/openalea_icon2.png"))
                parentItem.appendRow(item)
                self.old_models.append(name)
            
            # Scene
            parentItem = rootItem.child(2)
            for name in self.proj.scene:
                item = QtGui.QStandardItem(name)
                item.setIcon(QtGui.QIcon(":/images/resources/plant.png"))
                parentItem.appendRow(item) 
                self.old_scene.append(name)
        else:
            pass
