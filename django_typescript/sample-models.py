from django.db import models

# Should this be a reused type?
class TestCommonModel(models.Model):
    base_char_field = models.CharField(max_length=100)

    class Meta:
        abstract = True

class Test1ModelB(TestCommonModel):
    A = 'A'
    B = 'B'
    C = 'C'
    TEST_CHOICES_AS_TUPLES = (
        (A, 'a'),
        (B, 'b'),
        (C, 'c'),
    )
    TEST_CHOICES_AS_DICT = {
        A: 'a',
        B: 'b',
        C: 'c',
    }
    choice_tuple_field = models.CharField(max_length=100, choices=TEST_CHOICES_AS_TUPLES)
    choice_dict_field = models.CharField(max_length=100, choices=TEST_CHOICES_AS_DICT)
    
class Test1ModelF(TestCommonModel):
    name = models.CharField(max_length=100)
    
# Create your models here.
class Test2ModelA(models.Model):
    name = models.CharField(max_length=100)
    relationship = models.OneToOneField(
        Test1ModelB,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    
class Test2ModelE(models.Model):
    name = models.CharField(max_length=100)
    relationship = models.OneToOneField(
        Test1ModelF,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    
class Test3ModelC(models.Model):
    name = models.CharField(max_length=100)
    host = models.ForeignKey(Test2ModelA, on_delete=models.CASCADE)
    
class Test3ModelD(models.Model):
    name = models.CharField(max_length=100)
    host = models.ForeignKey(Test2ModelA, on_delete=models.CASCADE)