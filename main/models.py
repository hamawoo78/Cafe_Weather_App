from django.db import models
from django.utils import timezone

# Create your models here.

class Shop(models.Model):
    location = models.CharField(max_length=200, verbose_name='地域')
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True,verbose_name='緯度')
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True,verbose_name='経度')


    def __str__(self):
        return self.location

class Data(models.Model):
    location = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='地域')
    sales = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='売り上げ')
    Temp = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='気温')
    humid = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='湿度')
    date = models.DateTimeField(null=False)

    def save(self, *args, **kwargs):
        # If the date field is not set, set it to the current date and time
        if not self.date:
            self.date = timezone.now()
        super(Data, self).save(*args, **kwargs)

    
