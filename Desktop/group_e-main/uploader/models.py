from django.db import models


class Image(models.Model):
    title = models.CharField('タイトル', max_length=255)
    file = models.ImageField('ファイル')

    def __str__(self):
        return self.title
