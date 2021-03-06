#Copyright (C) 2012  Chris Marsh

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

import gdal
from gdalconst import *

from mainwindow import *
import mpl_view 
import crhmtools as ct
from module_loader import *
from lctreeview import *
from hru_details import *
from properties import *


class MainWindow(QMainWindow,Ui_MainWindow):

    def __init__(self):

        super(MainWindow,self).__init__()
        self.setupUi(self)
        self.setWindowTitle("CRHM Tools - 0.0.4b")
        
        #initialize the member variables
        #---------------------------------
        self.basin = ct.terrain.basin()        
        self.generated_lc = {}
        self.import_files = {}  #holds the loaded & imported files        
        self.current_fig = '' #name of what we are plotting 
        self.current_fig_item = None #reference to the QItem for the current figure (saves us having to look it up each time)    
        
        #--------------------------------
        #load the dynamic modules
        self.loader = module_loader()
        p =os.getcwd()
        self.loader.enumerate(os.path.join(p,'modules'))              
       
       
        #need to do the mpl init here otherwise it doesn't take up the full central widget
        self._init_mpl_view()

        self._init_treeviews()
        self._init_menus()


        self._set_layout()
        self.showMaximized()

        self.statusBar.showMessage('Ready')

    #handle the snigleclick  on the module tree and show the module description in the statusbar
    def _modtree_show_tip(self, item):
        try:
            self.statusBar.showMessage(self.loader(self.mod_model.itemFromIndex(item).text()).description)
        except KeyError: #we need to handle the case where the user clicks the main parent item, which isn't a module
            self.statusBar.showMessage(self.mod_model.itemFromIndex(item).text() + ' toolbox')

    #handle the double click on the module tree and run the selected module
    def _modtree_run_module(self, item):
        try:
            name = self.mod_model.itemFromIndex(item).text()
            module = self.loader.load(name, self.import_files,self.generated_lc)
            lc = module.show_ui()
            if lc != None:
                self.generated_lc[lc.get_name()] = lc
                #self.basin.add_landclass(lc)
                parent = self.lc_model.findItems('From functions').pop()
                item  = QStandardItem(lc._name)
                item.setDragEnabled(True)
                item.setDropEnabled(False)
                parent.appendRow(item)                        
        except KeyError: #we need to handle the case where the user clicks the main parent item, which isn't a module
            #unclear why this doesn't actually expand it.
            expand = not(self.treeView.isExpanded(self.treeView.currentIndex()))
            self.treeView.setExpanded(item,expand)

    #setup the tree view with the initial items
    def _init_treeviews(self):

        #initialize the landclass treeview
        #----------------------------------
        self.lc_model = LCTreeViewModel()
        self.lc_treeview.setModel(self.lc_model)
        parent = self.lc_model.invisibleRootItem()
        parent.setDropEnabled(False)        

        self.lc_model.insert_at_root('Imported files')
        self.lc_model.insert_at_root('From functions')
        self.lc_model.insert_at_root('Primary land classes',drop=True)
        self.lc_model.insert_at_root('Secondary land classes',drop=True)
        self.lc_model.insert_at_root('Generated HRUs')      
        
        #landclass tree right-click context menu
        self.lc_treeview.customContextMenuRequested.connect(self._context_menu)        

        #initialize the module treeivew
        #------------------------------
        self.mod_model = QtGui.QStandardItemModel()
        self.treeView.setModel( self.mod_model)
        parent =  self.mod_model.invisibleRootItem()
        
        row=0
        #loop through all the modules and add them to the tree
        for obj in self.loader:
            module = obj[1] #get the actualy module shell 
            #try to find the category in the tree
            index = self.mod_model.findItems(module.category)

            if index == []: #missing this category, so add it
                parent = self.mod_model.invisibleRootItem()
                item = QStandardItem(module.category)

                parent.appendRow(item)
                parent = item #make the parent the new category
            else:
                parent = index.pop() #because this returns a list, we need the only item in this list. Multiple finds shouldn't happen (famous last words)
                
            #add the tool to the view        
            name = QStandardItem(module.name)
            parent.appendRow(name)
            


        #connect the double click event to the .run() of the module
        self.treeView.doubleClicked.connect(self._modtree_run_module)
        #connect single click event to the .description of the module and show it
        self.treeView.clicked.connect(self._modtree_show_tip)
        #sort the tree
        self.treeView.sortByColumn(0,Qt.AscendingOrder)
        
        

    #set up the matplotlib view
    def _init_mpl_view(self):
        self.plot_widget = QWidget()
        self.mpl_widget = mpl_view.mpl_widget(self.plot_widget )

    #initialize the top menus
    def _init_menus(self):

        #Import a file
        self.actionImport_file.triggered.connect(self._import_file)

        #Generate a HRU
        self.actionGenerate_HRUs.triggered.connect(self._gen_hrus)
        
        self.actionClose.triggered.connect(self.close)
        
        self.actionHRU_paramaters.triggered.connect(self._open_hru_details)
        
        self.actionHRU_raster.triggered.connect(self._save_hru_to_raster)
        self.actionHRU_parameters.triggered.connect(self._save_hru_params)
        
        self.actionHRU_vector.triggered.connect(self._save_hru_to_vector)

    #set the layouts
    def _set_layout(self):
        hbox = QHBoxLayout()
        hbox.addWidget(self.mpl_widget.canvas)

        self.plot_widget.setLayout(hbox)                
        self.setCentralWidget(self.plot_widget)       
        self.lc_treeview.resizeColumnToContents(0)
        self.lc_treeview.resizeColumnToContents(1)
    
    def _sec_landclass(self):
        #load the list of secondary landclasses & populate a list of them
        slc = self.lc_model.findItems('Secondary land classes').pop() #comes back as a list, but we know there is only 1
        
        secondary_lc=[]
        for i in range(0,slc.rowCount()):
            secondary_lc.append(slc.child(i).text())        
        if len(secondary_lc) == 0 or self.basin._num_hrus == 0:
            self.statusBar.showMessage('No secondary landclasses or no HRUs')
            return
        return secondary_lc    

    def _open_hru_details(self):
        
        if self.basin.get_num_hrus() == 0:
            self.statusBar.showMessage('No HRUs')
            return
        
        
        secondary_lc = self._sec_landclass()
        wnd = HRUDetails(self,self.basin,secondary_lc,self.import_files,self.generated_lc)
        wnd.show()

        
        
    #Generate the HRU
    def _gen_hrus(self):
        self.statusBar.showMessage('Creating HRUs...')

        if self.basin._hrus != None:
            #reset the basin
            del self.basin
            self.basin = ct.terrain.basin()  
            
            parent = self.lc_model.findItems('Generated HRUs').pop()
            parent.removeRow(0)
                  
        
        
        p = self.lc_model.findItems('Primary land classes').pop()
        
        for i in range(0,p.rowCount()):
            lc = None
            try: #is this from our generated files?
                lc = self.generated_lc[p.child(i).text()]
            except: #must be from imported files
                lc = self.import_files[p.child(i).text()]
            
            self.basin.add_landclass(lc)
            
        #Ensure we have primary landclasses
        if self.basin.get_num_landclass() == 0:
            self.statusBar.showMessage('No landclasses')
            return
        

        #call the actual creation routine
        self.basin.create_hrus()

        #add to tree
        parent = self.lc_model.findItems('Generated HRUs').pop()
        parent.appendRow(QStandardItem('HRU'))
        self.statusBar.showMessage('Done')
        
        #self.actionGenerate_HRUs.setEnabled(False)

    #import a raster file 
    def _import_file(self):
        #the file to open
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file')    
        #bail on cancel
        if fname == '':
            return                
        
        
        self.statusBar.showMessage('Loading '+fname)
        name,ext = os.path.splitext(os.path.split(fname)[-1])

        #bail if we have already loaded this file.
        if self.import_files.has_key(name):
            self.statusBar.showMessage('File already imported')
            return
        
        #add to  the list
        self.import_files[name] = ct.terrain.landclass()
        self.import_files[name].open(fname)
        self.import_files[name].set_creator('Import')
        
        self.statusBar.showMessage('Done')

        #add to the treeview
        parent = self.lc_model.findItems('Imported files').pop()
        item = QStandardItem(name)
        item.setDropEnabled(False)
        item.setDragEnabled(True)
        it = parent.appendRow(item)
        self.lc_treeview.expand(parent.index())           
        
        if self.current_fig == '':
            self.plot(name,self.import_files[name]._raster)
            item.setData(1,QtCore.Qt.UserRole) #bold the item
            self.current_fig_item = item         #save the item so we can easily unbold it
            

    #rightclick context menu for the landclass treeview
    def _context_menu(self,position):
        menu = QMenu()
        indexes = self.lc_treeview.selectedIndexes()
        #get what we clicked
        item=self.lc_model.itemFromIndex(self.lc_treeview.currentIndex())

        #determine what level of the tree was selected
        if len(indexes) > 0:           

            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1                
        #if level == 0 and item.text() == 'Generated HRUs':
            #menu.addAction('Generate HRUs from primary')
        if level == 0 and item.text() == 'Imported files':
            menu.addAction('Import file')
        elif level == 1:
            if index.data() == 'Generated HRUs':
                menu.addAction("Show HRU")
            elif index.data() == 'Secondary land classes':
                menu.addAction('Remove')
            elif index.data() == 'Imported files':
                menu.addAction('Show')
                menu.addAction('Close')
            elif index.data() == 'Primary land classes' or index.data() == 'From functions':
                act = menu.addAction("Show classified")
                
                #disable this option if the land class is not yet classified, i.e., came from a function that doesn't classify
                lc = None
                try:
                    lc = self.import_files[item.text()]
                except:
                    lc = self.generated_lc[item.text()]
                
                if lc._classified == None:
                    act.setDisabled(True)
                    
                menu.addAction("Show non-classified")
                
                menu.addAction("Remove")
                
                menu.addAction('Properties')
                


        #show menu at the point we clicked
        a=menu.exec_(self.lc_treeview.viewport().mapToGlobal(position))

        #no click, bail
        if not a:
            return

        #do the action
        if a.text() == 'Import file':
            self._import_file()
        elif a.text() == 'Show':
            self._plot_imported(item.text())
        elif a.text() == 'Close':
            del self.import_files[item.text()]
            
            if self.current_fig == item.text():
                    self.mpl_widget.clear()
                    self.current_fig_item = None
            
            self.lc_model.removeRow(item.row(),parent=item.parent().index()) 
        elif a.text() == 'Show HRU':
            self._plot_hru()
        elif a.text() == 'Show classified':
            self._plot_landclass(item.text(),True)
        elif a.text() == 'Show non-classified':
            self._plot_landclass(item.text(),False)
        elif a.text() == 'Properties':
            try: #did it come from the generated stuff?
                prop = Properties(self.generated_lc[item.text()])
            except: #must be an imported file
                prop = Properties(self.import_files[item.text()])
            prop.window.exec_()
        elif a.text() == 'Remove':

            #remove plot if we are currently showing it
            if self.current_fig == item.text():
                self.mpl_widget.clear()
                self.current_fig_item = None

            if index.data() == 'From functions':
                del self.generated_lc[item.text()]
            
            self.lc_model.removeRow(item.row(),parent=item.parent().index())   
            
            
                
        elif a.text() == 'Generate HRUs from primary':
            self._gen_hrus()
        
        #set the currently shown figure to have bolded text
        if 'Show' in a.text():
            if  self.current_fig_item:
                self.current_fig_item.setData(0,QtCore.Qt.UserRole) #unbold 
                
            item.setData(1,QtCore.Qt.UserRole)
            self.current_fig_item = item

    #base plotting function
    def plot(self,name,raster,ticks=[],labels=[]):
        self.statusBar.showMessage('Plotting...')
        
        self.current_fig = name
        self.mpl_widget.plot(raster,ticks,labels)
        self.statusBar.showMessage('Done')     

    #show the hru
    def _plot_hru(self):
        ticks = range(1,self.basin.get_num_hrus()+1)
        labels = ['HRU ' + str(i) for i in ticks]
        self.plot('hrus',self.basin._hrus._raster,ticks,labels)
        
    #show the imported file
    def _plot_imported(self, name):

        r=self.import_files[name].get_raster()
        self.plot('imported_'+name,r)

    #show a landclass, either classified or not
    def _plot_landclass(self,name,classified=True):

        if classified:
            r = self.generated_lc[name].get_classraster()
            self.plot(name,r,ticks=list(range(1,self.generated_lc[name].get_nclasses()+1)),labels=self.generated_lc[name].get_classes_str())
        else:
            r = self.generated_lc[name].get_raster()
            self.plot(name,r)


    def _save_hru_to_raster(self):
        if self.basin.get_num_hrus() != 0:
            fname = QFileDialog.getSaveFileName(self, caption="Save Raster",  filter="Raster Files (*.tif)")            
            self.basin._hrus.save_to_file(fname[0])
        else:
            self.statusBar.showMessage('No current HRUs')
            
    def _save_hru_to_vector(self):
        if self.basin.get_num_hrus() != 0:
            try:
                    fname = QFileDialog.getSaveFileName(self, caption="Save Vector",  filter="Vector Files (*.shp)")            
                    self.basin._hrus.save_to_vector(fname[0])  
            except IOError as e:
                msg = QMessageBox()
                msg.setText(str(e))
                msg.exec_()
                return                
        else:
                    self.statusBar.showMessage('No current HRUs')        
                    
    #save paramters to csv   
    def _save_hru_params(self):
        if self.basin.get_num_hrus() != 0:
            fname = QFileDialog.getSaveFileName(self, caption="Save Parameters",  filter="CSV Files (*.csv)")  
            try:
                f = open (fname[0], 'w')
            except Exception as e:
                msg = QMessageBox()
                msg.setText(str(e))
                msg.exec_()
                return
        else:
            self.statusBar.showMessage('No current HRUs')
            return
        
        nhru = self.basin.get_num_hrus()
        secondary_lc = self._sec_landclass()
        f.write(',') #skip a cell so the table looks good and lines up
        for i in range(0,nhru):
            f.write('HRU ' + str(i+1) +',')
        f.write('\n')
            

        
        for j in range(0,len(secondary_lc)):
            f.write('Mean of ' + secondary_lc[j]+',')    
            
            for i in range(0,nhru):
                    try:
                        mean = np.mean(self.import_files[secondary_lc[j]].get_raster()[self.basin._hrus._raster   == i+1])
                    except:
                        mean = np.mean(self.generated_lc[secondary_lc[j]].get_raster()[self.basin._hrus._raster   == i+1])
                        
                    item = '{0:.2f}'.format(mean)
                    f.write(item+',')  

            f.write('\n')  
        
 
            
        f.write('Area (km^2),')
        #calculate the area of each HRU
        for i in range(0,nhru):
            total = (self.basin._hrus._raster  == i+1).sum()
            total = total * abs(self.basin._hrus.get_resolution()[0]*self.basin._hrus.get_resolution()[1]) / 10**6 # to km^2
                
            item = '{0:.2f}'.format(total)
            f.write(item+',')
   

        f.write('\n')    
        f.close()

    