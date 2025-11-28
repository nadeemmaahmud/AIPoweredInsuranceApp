from django.db import models
from users.models import CustomUser

class Case(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type_of_injury = models.CharField(max_length=255)
    date_of_incident = models.DateField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class CaseFile(models.Model):
    case = models.ForeignKey(Case, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="case_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)