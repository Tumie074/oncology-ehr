from django.contrib import admin
from .models import CamperCheckIn, CrewCheckIn, CrewIndemnity, MedShackVisit, NearMissReport

for m in (CamperCheckIn, MedShackVisit, CrewCheckIn, CrewIndemnity):
    admin.site.register(m)


@admin.register(NearMissReport)
class NearMissAdmin(admin.ModelAdmin):
    """Read-only: near-miss reports are append-only."""
    list_display = ('camper_name', 'event_at', 'reporter_name')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
