from django.contrib import admin
from django.urls import include, path

handler403 = 'accounts.views_errors.forbidden'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('notes/', include('campnotes.urls')),
    path('medication/', include('medication.urls')),
    path('forms/', include('records.urls')),
]
