from django.db import models


class Attachments(models.Model):
    fileno = models.BigAutoField(primary_key=True)
    filename = models.CharField(max_length=256)
    filedata = models.BinaryField()
    extension = models.CharField(max_length=16)

    class Meta:
        managed = False
        db_table = 'attachments'


class ApplicationDoc(models.Model):
    regno = models.BigAutoField(primary_key=True)
    fileno = models.ForeignKey(Attachments, models.DO_NOTHING, db_column='fileno')
    registration_no = models.CharField(max_length=10)
    business_name = models.CharField(max_length=160)
    representative = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=2)

    class Meta:
        managed = False
        db_table = 'application_doc'


class TemporaryCode(models.Model):
    regno = models.BigAutoField(primary_key=True)
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    expired_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'temporary_code'
