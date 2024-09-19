from django.core.management.base import BaseCommand
import django.apps
import subprocess
import os
from django.conf import settings
from django_typescript.management.typewriter import typewriter

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
    Find name of primary key field
"""
def get_primary_key_field(model):
    for field in model._meta.local_fields:
        if field.primary_key:
            return field.attname
        
    return None

def hyphenate_model_name(model):
    model_name = model.__name__
    
    hyphenated = model_name[0].lower()
    
    for character in model_name[1:]:
        if character.isupper() or character.isdigit():
            hyphenated += "-" + character.lower()
        elif character.islower():
            hyphenated += character
        else:
            raise ValueError("Unsupported character (%s) in name (%s) for model class: %s" % (character, model_name, model))
            
    return hyphenated
     
class Command(BaseCommand):
    help = "Generates types for your application's models"
    
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
    def write_types(self, dependency_tree):
        generated_files = []
            
        for node in dependency_tree['nodes']:
            model = node[0]
            # TODO: Use hyphentated case for file
            name = model.__name__
            dependencies = node[1]
            
            # TODO: Write temporary files, validate, and then move to final destination
            file_name = "%s.d.ts" % hyphenate_model_name(model)
            self.stdout.write('Writing file %s' % file_name)
            with typewriter(file_name, "w") as file:
                
                dependency_names = [dep.__name__ for dep in dependencies]
                
                if len(dependency_names) > 0:
                    for dependency in dependency_names:     
                        file.write_import(dependency, dependency)
                
                file.write_new_line()
                
                # TODO: Capture all fields
                fields = []
                for local_field in model._meta.local_fields:
                    field_name = local_field.attname
                    
                    if local_field.is_relation:
                        related_model = local_field.related_model
                        primary_key = get_primary_key_field(related_model)
                        value = "%s[\"%s\"]" % (related_model.__name__, primary_key)
                        fields.append((field_name, value))
                    else:  
                        field_type = type_mappings[local_field.get_internal_type()]
                        fields.append((field_name, field_type))
                
                file.write_export(name, fields)
                
                # TODO: Hook in tsc output for value
                subprocess.run(["tsc", file.name, "--noEmit"], check=True)
                generated_files.append(file.name)
        
        if 'children' in dependency_tree:
            generated_files += self.write_types(dependency_tree['children'])
        
        return generated_files
    
    """
        Construct a tree of models in order that they can be processed
    """
    def create_module_tree(self, models):
        tree = {}
        visited = []
        
        for model in models:
            build_node(model, tree, visited)
        
        self.stdout.write(self.style.SUCCESS('%s models found for application' % len(visited)))
        
        return tree;

    def handle(self, *args, **options):
        
        if not hasattr(settings, 'DJANGO_TYPESCRIPT_DIR'):
            raise Exception("DJANGO_TYPESCRIPT_DIR is not defined in settings")
        
        if not os.path.exists(settings.DJANGO_TYPESCRIPT_DIR):
            os.makedirs(settings.DJANGO_TYPESCRIPT_DIR)
            
        os.chdir(settings.DJANGO_TYPESCRIPT_DIR)
        
        application_models = django.apps.apps.get_models()
        
        self.stdout.write('Searching for models in application')
        module_tree = self.create_module_tree(application_models)
        self.stdout.write('Writing types to files')     
        self.write_types(module_tree)
        self.stdout.write(self.style.SUCCESS('Types generated successfully'))