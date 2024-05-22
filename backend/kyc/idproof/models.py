from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Extend the User model to include the country field
class CountryModel(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='countries')

    def __str__(self):
        return self.name
class DocumentSetModel(models.Model):
    name_of_document = models.CharField(max_length=255)
    countries = models.ManyToManyField(CountryModel)
    has_backside = models.BooleanField(default=False)
    ocr_labels = models.TextField()  # Store JSON as string

    def __str__(self):
        return self.name_of_document

class CustomerModel(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    surname = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    nationality = models.ForeignKey(CountryModel, on_delete=models.PROTECT)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.surname}"

class CustomerDocumentModel(models.Model):
    customer = models.ForeignKey(CustomerModel, on_delete=models.CASCADE)
    attached_file = models.FileField(upload_to='customer_documents/')
    extracted_json = models.TextField()  # Store JSON as string
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Document for {self.customer}"
