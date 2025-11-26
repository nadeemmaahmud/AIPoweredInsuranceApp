from django.db import models
from django.db.models import JSONField
from users.models import CustomUser
from django.core.files.storage import default_storage

class Case(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type_of_injury = models.CharField(max_length=255)
    date_of_incident = models.DateField()
    description = models.TextField()
    files = JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save_file(self, file):
        filename = default_storage.save(f"case_files/{file.name}", file)
        return filename