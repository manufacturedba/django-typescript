# Django Typescript

Django Typescript generates types against your Django application models

**Please note that this is a work in progress and is not yet ready for real use.**

## Getting Started

### Getting It

TODO: Publish package when ready for 0.1.0

### Installing It

To enable `django_typescript` in your project you need to add it to `INSTALLED_APPS` in your projects
`settings.py` file:

```python
INSTALLED_APPS = (
    ...
    'django_typescript',
    ...
)
```
    
You will also need to specify a directory to store generated typings:

```python
DJANGO_TYPESCRIPT_DIR='types'
```


### Using It

Generate types:

    $ python manage.py generate_types