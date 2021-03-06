import imp
import os
import inspect
import sys

#module shell contains the 'shell' of a module. i.e., just the information
class module_shell(object):
    def __init__(self):
        self.name = ''
        self.version = '0.0'
        self.description = ''
        self.author = ''
        self.category = ''
        self.file_name = ''
        
#Handles loading of the dynamic modules
class module_loader(object):
    def __init__(self):

        self.modules = {}
    def __call__(self,name):
        return self.modules[name]
    
    def enumerate(self,path):

        files = os.listdir(path)	
        for f in files:
            name,ext = os.path.splitext(os.path.split(f)[-1])

            if ext.lower() == '.py':
                shell = module_shell()
                shell.path = os.path.join(path,name+ext)
                shell.file_name = name
                temp = None
                # we need this information to populate the treeview in the main gui
                #class name MUST have mod_ in it
                py_mod = imp.load_source( shell.file_name, shell.path )
                for name,obj in inspect.getmembers(py_mod,inspect.isclass):
                    if 'mod_' in name:
                        #instaniate this 
                        temp = eval('py_mod.'+name+'(None,None)')
                shell.name = temp.name
                shell.version = temp.version
                shell.description = temp.description
                shell.author = temp.author
                shell.category = temp.category
                self.modules[shell.name] = shell

        return self.modules 	
    
    #loads a module
    def load(self,name,imported_files,generated_lc):

        py_mod = imp.load_source(self.modules[name].file_name, self.modules[name].path)

        #class name MUST have mod_ in the name
        for name,obj in inspect.getmembers(py_mod,inspect.isclass):
            if 'mod_' in name:
                #instaniate this 
                mod = eval('py_mod.'+name+'(imported_files,generated_lc)')
                return mod
        
        return None  

    def __iter__(self):
        for f in self.modules.items():
            yield f
            