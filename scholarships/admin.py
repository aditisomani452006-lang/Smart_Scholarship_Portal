from django.contrib import admin
from .models import StudentProfile, Scholarship, Application, Notification

admin.site.register(StudentProfile)
admin.site.register(Scholarship)
admin.site.register(Application)
admin.site.register(Notification)
