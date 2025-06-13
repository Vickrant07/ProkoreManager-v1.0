from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(ProjectDetails)

admin.site.register(WindowStatusID)

admin.site.register(CwiStatusID)

admin.site.register(OilBoilerStatusID)

admin.site.register(OilTankStatusID)

admin.site.register(EwiStatusID)

admin.site.register(PlumbingStatusID)

admin.site.register(IwiStatusID)

admin.site.register(AirtightnessStatusID)

admin.site.register(RtvStatusID)

admin.site.register(MevStatusID)

admin.site.register(AtticStatusID)

admin.site.register(DraughtProofingStatusID)


admin.site.register(CompanyProjectStages)

admin.site.register(QcStages)

