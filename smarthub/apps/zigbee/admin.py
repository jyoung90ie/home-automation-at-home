from django.contrib import admin
from . import models


class ZigbeeDeviceAdmin(admin.ModelAdmin):
    pass


class ZigbeeMessageAdmin(admin.ModelAdmin):
    pass


class ZigbeeLogAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.ZigbeeDevice, ZigbeeDeviceAdmin)
admin.site.register(models.ZigbeeMessage, ZigbeeMessageAdmin)
admin.site.register(models.ZigbeeLog, ZigbeeLogAdmin)
