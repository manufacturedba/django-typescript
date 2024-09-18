from django.core.management.base import BaseCommand
import django.apps
import subprocess
import os
from django.conf import settings
import json
import re
from django_typescript.management.typewriter import TypeWriter

def writeLine(file, line):
    file.write(line + "\n")

# TODO: Map from class reference to string
# TODO: Open interface from user to specify their own mappings
type_mappings = {
    'CharField': 'string',
    'BigAutoField': 'number',
    'TextField': 'string',
    'AutoField': 'number',
    'IntegerField': 'number',
    'FloatField': 'number',
    'DecimalField': 'number',
    'BooleanField': 'boolean',
    'DateField': 'string',
    'DateTimeField': 'string',
    'TimeField': 'string',
    'DurationField': 'string',
    'UUIDField': 'string',
    'PositiveSmallIntegerField': 'number',
}

relationship_types = [
    'ForeignKey',
    'OneToOneField',
    'ManyToManyField',
]

"""
    For a given model, work through dependencies and add self as node
"""
def build_node(model, layer, visited):    
    dependencies = []
    traversed_dependencies = []
    
    for local_field in model._meta.local_fields:
        if local_field.get_internal_type() in relationship_types:
            traversed_dependencies.append(local_field.related_model)
            dependencies.append(local_field.related_model)
            
            # Visit dependency first
            if local_field.related_model not in visited:
                build_node(local_field.related_model, layer, visited=visited)
            
            # Until all dependencies are found on tree going down
            while len(traversed_dependencies) > 0:
                # Dependencies after checking layer
                node_classes = [node[0] for node in layer['nodes']]
                overlap = list(set(traversed_dependencies) & set(node_classes))
                traversed_dependencies = list(set(traversed_dependencies) ^ set(overlap))
                
                # Also stop if we have to create a new layer
                if 'children' not in layer:
                    layer['children'] = {}
                    layer = layer['children']
                    break
                else:
                    layer = layer['children']
                    
                        
    # Being revisited by a child
    if model in visited:
        return
               
    visited.append(model)
    
    if 'nodes' not in layer:
        layer['nodes'] = []
        
    layer['nodes'].append((model, dependencies))
     
"""
    Construct a tree of models in order that they can be processed
"""
def create_module_tree(models):
    tree = {}
    visited = []
    
    for model in models:
        build_node(model, tree, visited)
    
    return tree;

"""
    Find name of primary key field
"""
def get_primary_key_field(model):
    for field in model._meta.local_fields:
        if field.primary_key:
            return field.attname
        
    return None

"""
    Writes types against a given module tree
    {
        nodes: [
            (model, [dependencies])
        ],
        children: {
            nodes: [
                (model, [dependencies])
            ],
            children: {
                ...
            }
        }
    }
"""  
def write_types(dependency_tree):
    generated_files = []
        
    for node in dependency_tree['nodes']:
        model = node[0]
        # TODO: Use hyphentated case for file
        name = model.__name__
        dependencies = node[1]
           
        # TODO: Write temporary files, validate, and then move to final destination
        # TODO: Write hyphenated name
        file_name = "%s.d.ts" % name
        with open(file_name, "w") as temp_js:
            typewriter = TypeWriter(temp_js)
            
            dependency_names = [dep.__name__ for dep in dependencies]
            
            if len(dependency_names) > 0:
                for dependency in dependency_names:     
                    typewriter.write_import(dependency, dependency)
            
            typewriter.write_new_line()
            
            # TODO: Capture all fields
            fields = []
            for local_field in model._meta.local_fields:
                field_name = local_field.attname
                internal_type = local_field.get_internal_type()
                relationship_type = internal_type in relationship_types
                
                if local_field.is_relation:
                    related_model = local_field.related_model
                    primary_key = get_primary_key_field(related_model)
                    value = "%s[\"%s\"]" % (related_model.__name__, primary_key)
                    fields.append((field_name, value))
                else:  
                    field_type = type_mappings[local_field.get_internal_type()]
                    fields.append((field_name, field_type))
            
            typewriter.write_export(name, fields)
            
            # TODO: Hook in tsc output for value
            subprocess.run(["tsc", temp_js.name, "--noEmit"], check=True)
            generated_files.append(temp_js.name)
    
    if 'children' in dependency_tree:
        generated_files += write_types(dependency_tree['children'])
    
    return generated_files
        
        
class Command(BaseCommand):
    help = "Generates types for your application's models"
    
    def handle(self, *args, **options):
        
        if not hasattr(settings, 'DJANGO_TYPESCRIPT_DIR'):
            raise Exception("DJANGO_TYPESCRIPT_DIR is not defined in settings")
        
        if not os.path.exists(settings.DJANGO_TYPESCRIPT_DIR):
            os.makedirs(settings.DJANGO_TYPESCRIPT_DIR)
            
        os.chdir(settings.DJANGO_TYPESCRIPT_DIR)
        
        application_models = django.apps.apps.get_models()
        
        self.stdout.write(
            self.style.NOTICE("Generating types")
        )
        
        module_tree = create_module_tree(application_models)
                
        self.stdout.write(
            self.style.SUCCESS("\n".join(write_types(module_tree)))
        )