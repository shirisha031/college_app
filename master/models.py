"""
Definition of models.
"""

from django.db import models


class ExcelUpload(models.Model):
    file = models.FileField(upload_to='excel_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class StudentRecord(models.Model):
    student_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_relation = models.CharField(max_length=50)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.student_name} ({self.student_id})"
class SentMessage(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    send_sms = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    department = models.CharField(max_length=100)
    sent_at = models.DateTimeField(auto_now_add=True)
      # 👇 Add this field
    status = models.CharField(
        max_length=20,
        choices=[('Delivered', 'Delivered'), ('Not Delivered', 'Not Delivered'), ('Pending', 'Pending')],
    )

    def __str__(self):
        return f"{self.subject} ({self.department})"