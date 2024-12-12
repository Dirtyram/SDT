from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    calorie_limit = models.IntegerField(null=True, blank=True)

class CalorieEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    food = models.CharField(max_length=255)
    calories = models.IntegerField()
