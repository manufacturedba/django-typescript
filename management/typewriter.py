class TypeWriter:
    def __init__(self, file):
        self.file = file

    def _write_line(self, line):
        self.file.write(line)
        
    def _write_new_line(self, line):
        self._write_line(line + "\n")
    
    def write_new_line(self):
        self._write_new_line("")
        
    def write_import(self, module, filename):
        self._write_new_line("import { %s } from './%s'" % (module, filename))
        
    def write_export(self, module, keys):
        self._write_new_line("export type %s = {" % module)
        
        for key in keys:
            self._write_new_line("%s: %s" % (key[0], key[1]))
        
        self._write_new_line("}")