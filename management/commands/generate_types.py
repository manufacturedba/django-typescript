from django.core.management.base import BaseCommand
import django.apps
import os
from django.conf import settings
from django_typescript.management.typewriter import typewriter
from django.db.models import CharField, BigAutoField, TextField, AutoField, IntegerField, FloatField, DecimalField, BooleanField, DateField, DateTimeField, TimeField, DurationField, UUIDField, PositiveSmallIntegerField, EmailField
import inspect

# TODO: Open interface from user to specify their own mappings
# TODO: Create classes in place of primitives that have client settable properties 
type_mappings = {
    CharField: 'string',
    BigAutoField: 'number',
    TextField: 'string',
    AutoField: 'number',
    IntegerField: 'number',
    FloatField: 'number',
    DecimalField: 'number',
    BooleanField: 'boolean',
    DateField: 'string',
    DateTimeField: 'string',
    TimeField: 'string',
    DurationField: 'string',
    UUIDField: 'string',
    PositiveSmallIntegerField: 'number',
    EmailField: 'string',
}

def build_node(model, layer, visited):
    """
        For a given model, work through dependencies and add self as node
    """
    dependencies = []
    traversed_dependencies = []
    
    for local_field in model._meta.local_fields:
        # TODO: Support recursive relationships for foreign keys i.e. models.ForeignKey("self")
        if local_field.is_relation:
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

def hyphenate_name(name):
    hyphenated = name[0].lower()
    
    for character in name[1:]:
        if character.isupper() or character.isdigit():
            hyphenated += "-" + character.lower()
        elif character.islower():
            hyphenated += character
        else:
            raise ValueError("Unsupported character (%s) in name (%s)" % (character, name))
            
    return hyphenated
     
class Command(BaseCommand):
    help = "Generates types for your application's models"
     
    def write_types(self, dependency_tree):
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
        
        # From this point we move and stay within the write directory
        os.chdir(settings.DJANGO_TYPESCRIPT_DIR)
        
        generated_files = []
            
        for node in dependency_tree['nodes']:
            model = node[0]
            dependencies = node[1]
            
            # TODO: Write temporary files, validate, and then move to final destination
            model_name = model.__name__
            # TODO: Switch to application or module as name of file
            file_name = "%s.d.ts" % hyphenate_name(model_name)
            self.stdout.write('Writing file %s' % file_name)
            # TODO: Consolidate types within the same module to same file
            with typewriter(file_name, "w") as typer:
                typer.set_name(model_name)
                
                dependency_names = [dep.__name__ for dep in dependencies]
                
                if len(dependency_names) > 0:
                    for dependency in dependency_names:
                        typer.add_import(dependency, hyphenate_name(dependency)) 
                
                def get_field_type(field):
                    if field.is_relation:
                        related_model = field.related_model
                        primary_key = get_primary_key_field(related_model)
                        field_type = "%s[\"%s\"]" % (related_model.__name__, primary_key)
                    elif field.choices:
                        if isinstance(field.choices, dict):
                            field_type = (" | ").join(["\"%s\"" % field.choices[key] for key in field.choices.keys()])
                        else:
                            field_type = (" | ").join(["\"%s\"" % choice[1] for choice in field.choices])
                    else:  
                        field_type = type_mappings[local_field.__class__]
                        
                    if local_field.null:
                        field_type += " | null"
                    if local_field.blank:
                        field_type += " | undefined"
                        
                    return field_type
                    
                # TODO: Capture all fields
                fields = []
                for local_field in model._meta.local_fields:
                    field_name = local_field.attname
                    
                    fields.append((field_name, get_field_type(local_field)))
                
                typer.add_properties(fields)
                
                generated_files.append(file_name)
        
        if 'children' in dependency_tree:
            generated_files += self.write_types(dependency_tree['children'])
        
        return generated_files
    
    def create_module_tree(self, models):
        """
            Construct a tree of models in order that they can be processed
        """
        tree = {}
        visited = [] # Tracks every model we visit regardless of start-point
        
        # Have all models serve as a seed to build the tree
        # TODO: Have traversal exit early once the entry count reachesthe 
        # number of models in the application
        for model in models:
            build_node(model, tree, visited)
        
        self.stdout.write(self.style.SUCCESS('%s models found for application' % len(visited)))
        
        return tree;

    def add_arguments(self, parser):
        # Loosely intended for testing sample models
        parser.add_argument("model_file", nargs="?", type=str, help="Relative path to a model file.",)
        
    def handle(self, *args, **options):
        model_file_name = options["model_file"]
        
        if not hasattr(settings, 'DJANGO_TYPESCRIPT_DIR'):
            raise Exception("DJANGO_TYPESCRIPT_DIR is not defined in settings")
        
        if not os.path.exists(settings.DJANGO_TYPESCRIPT_DIR):
            os.makedirs(settings.DJANGO_TYPESCRIPT_DIR)
                    
        def filter_models(model):
            if model_file_name is None:
                return True
            else:
                filename = inspect.getfile(model)
                return filename == os.path.abspath(model_file_name)
            
        self.stdout.write('Getting for models in application')
        application_models = list(filter(filter_models, django.apps.apps.get_models()))
        
        # TODO: Try loading models dynamically by provided file before giving up
        if len(application_models) == 0:
            self.stdout.write(self.style.ERROR('No models found in application'))
            return
        
        self.stdout.write('Creating dependency mapping for models')
        module_tree = self.create_module_tree(application_models)
        self.stdout.write('Writing types to files')     
        self.write_types(module_tree)
        self.stdout.write(self.style.SUCCESS('Types generated successfully'))