from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username

class Image(models.Model):
    user = models.ForeignKey(User, related_name='images', on_delete=models.CASCADE)
    image_path = models.CharField(max_length=255)

    def __str__(self):
        return self.image_path