from django.contrib import admin
from . import models

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.CustomUser, UserAdmin)
