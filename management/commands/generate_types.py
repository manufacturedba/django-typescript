from django.core.management.base import BaseCommand
import django.apps
import subprocess
import os
from django.conf import settings

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
    'ForeignKey': 'number',
    'OneToOneField': 'number',
    'ManyToManyField': 'number[]',
    'PositiveSmallIntegerField': 'number',
}

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
        
        generated_files = []
        for model in application_models:
            # TODO: Use hyphentated case
            name = model.__name__
            
            # TODO: Write temporary files, validate, and then move to final destination
            with open("%s.d.ts" % name, "w") as temp_js:
                writeLine(temp_js, "export type %s = {" % name)

                # TODO: Capture all fields
                # TODO: Handle references to other models via imports
                for local_field in model._meta.local_fields:
                    field_name = local_field.attname
                    field_type = type_mappings[local_field.get_internal_type()]
                    writeLine(temp_js, "%s: %s" % (field_name, field_type))
                    
                writeLine(temp_js, "}")
                
                # TODO: Hook in tsc output for value
                subprocess.run(["tsc", temp_js.name, "--noEmit"], check=True)
                generated_files.append(temp_js.name)
                
                
        self.stdout.write(
            self.style.SUCCESS("\n".join(generated_files))
        )