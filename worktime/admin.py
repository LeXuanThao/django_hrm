from django.contrib import admin
from .models import WorkType

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'work_type', 'description')
    search_fields = ('employee__account__email', 'work_type')
    ordering = ('work_type',)

# Register your models here.
