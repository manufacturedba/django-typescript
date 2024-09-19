from string import Template

import_template = Template("import { $named_import } from './$module'\n")
export_template = Template("export type $module = {\n$properties}")
property_template = Template("  $key: $value\n")

class TypeWriter:
    def __init__(self, *args, **kwargs):
        self.imports = None
        self.properties = None
        self.type_name = None
        self.lines = ""
        self.file = open(*args, **kwargs)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        
        if self.type_name is None:
            raise ValueError("Type name must be set")
            
        if self.properties is None:
            raise ValueError("Empty type is not allowed. Set at least one property")
            
        if self.imports is not None:
            self._write_new_line(self.imports)
        
        self._write_new_line(export_template.substitute(module=self.type_name, properties=self.properties))
        
        self.file.write(self.lines)
        self.file.close()
    
    def _write_line(self, line):
        self.lines += line
        
    def _write_new_line(self, line):
        self._write_line(line + "\n")
    
    def _write_line_break(self):
        self._write_new_line("")
    
    def add_import(self, named_import, module):
        """
        Adds a single named import for a given module name
        Only relative paths are supported

        Args:
            named_import (string): Named import exported from module
            module (string): Module name and path
        
        Examples:
            >>> add_import("User", "models/user")
        """
        if self.imports is None:
            self.imports = ""
            
        self.imports += import_template.substitute(named_import=named_import, module=module)
    
    def add_properties(self, properties):
        """
        Adds properties to a type

        Args:
            properties (list((key, value))): List of properties as key-value tuples
        
        Examples:
            >>> add_properties([("name", "string"), ("age", "number")])
        """
        if self.properties is None:
            self.properties = ""
            
        for entry in properties:
            key, value = entry
            self.properties += property_template.substitute(key=key, value=value)
    
    def set_name(self, type_name):
        """
        Sets a type name for the single export of this module

        Args:
            type_name (string): Name of the type to be exported
        
        Examples:
            >>> set_name("Person")
        """
        self.type_name = type_name
        
    @property
    def name(self):
        return self.file.name
        
def typewriter(*args, **kwargs):
    return TypeWriter(*args, **kwargs)