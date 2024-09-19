# Django Typescript

Django Typescript generates typings against your Django application models

**Please note that this is a work in progress and is not yet ready for production.**

## Getting Started

This package has only been tested against Django 5.1

### Getting It

    $ pip install django-typescript

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