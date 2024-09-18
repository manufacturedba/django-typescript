from string import Template

import_template = Template("import { $module } from './$filename'")
export_open_template = Template("export type $module = {")
property_template = Template("$key: $value")
export_close_template = Template("}")

class TypeWriter:
    def __init__(self, *args, **kwargs):
        self.lines = ""
        self.file = open(*args, **kwargs)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.file.write(self.lines)
        self.file.close()
    
    def _write_line(self, line):
        self.lines += line
        
    def _write_new_line(self, line):
        self._write_line(line + "\n")
    
    def write_new_line(self):
        self._write_new_line("")
        
    def write_import(self, module, filename):
        self._write_new_line(import_template.substitute(module=module, filename=filename))
        
    def write_export(self, module, keys):
        self._write_new_line(export_open_template.substitute(module=module))
        
        for key in keys:
            self._write_new_line(property_template.substitute(key=key[0], value=key[1]))
        
        self._write_new_line(export_close_template.substitute())
    
    @property
    def name(self):
        return self.file.name
        
def typewriter(*args, **kwargs):
    return TypeWriter(*args, **kwargs)