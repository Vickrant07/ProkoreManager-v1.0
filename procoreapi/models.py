from django.db import models
from datetime import datetime
# from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class ProjectDetails(models.Model):
    project_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    project_number = models.CharField(max_length=20, unique=True, blank=False)
    project_name = models.CharField(max_length=100, blank=False)
    project_office = models.CharField(max_length=20 , blank=False, unique=False, default='WHS')
    project_stage = models.CharField(max_length=50, blank=False)
    GNI_STATUS = models.CharField(max_length=50, blank=False)
    ESB_STATUS = models.CharField(max_length=50, blank=False)
    QC_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    WINDOW_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    window_correspondence_id = models.IntegerField(default=0)
    CWI_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    cwi_correpondence_id = models.IntegerField(default=0)
    OIL_BOILER_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    oil_boiler_correspondence_id = models.IntegerField(default=0)
    OIL_TANK_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    oil_tank_correspondence_id = models.IntegerField(default=0)
    EWI_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    ewi_correspondence_id = models.IntegerField(default=0)
    PLUMBING_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    plumbing_correpondence_id = models.IntegerField(default=0)
    IWI_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A') 
    iwi_correspondence_id = models.IntegerField(default=0)
    AIRTIGHTNESS_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    airtightness_correspondence_id = models.IntegerField(default=0)
    RTV_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    rtv_correspondence_id = models.IntegerField(default=0)
    MEV_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    mev_correspondence_id = models.IntegerField(default=0)
    ATTIC_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    attic_correspondence_id = models.IntegerField(default=0)
    DRAUGHTPROOFING_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    draughtproofing_correspondence_id = models.IntegerField(default=0)
    Project_Manager = models.CharField(max_length=50, blank=False, unique=False, null=True, default='N/A')
    
class CorrespondenceTypeID(models.Model):
    correspondence_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    correspondence_name = models.CharField(max_length=100, blank=False)
    correspondence_abbreviation = models.CharField(max_length=100, blank=False)

class WindowStatusID(models.Model):
    window_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    window_status_name = models.CharField(max_length=50, blank=False)
    window_status_status = models.CharField(max_length=10, blank=False)
    
class CwiStatusID(models.Model):
    cwi_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    cwi_status_name = models.CharField(max_length=50, blank=False)
    cwi_status_status = models.CharField(max_length=10, blank=False)

class OilBoilerStatusID(models.Model):
    oil_boiler_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    oil_boiler_status_name = models.CharField(max_length=50, blank=False)
    oil_boiler_status_status = models.CharField(max_length=10, blank=False)
    
class OilTankStatusID(models.Model):
    oil_tank_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    oil_tank_status_name = models.CharField(max_length=50, blank=False)
    oil_tank_status_status = models.CharField(max_length=10, blank=False)

class EwiStatusID(models.Model):
    ewi_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    ewi_status_name = models.CharField(max_length=50, blank=False)
    ewi_status_status = models.CharField(max_length=10, blank=False)
    
class PlumbingStatusID(models.Model):
    plumbing_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    plumbing_status_name = models.CharField(max_length=50, blank=False)
    plumbing_status_status = models.CharField(max_length=10, blank=False)
    
class IwiStatusID(models.Model):
    iwi_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    iwi_status_name = models.CharField(max_length=50, blank=False)
    iwi_status_status = models.CharField(max_length=10, blank=False)
    
class AirtightnessStatusID(models.Model):
    airtightness_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    airtightness_status_name = models.CharField(max_length=50, blank=False)   
    airtightness_status_status = models.CharField(max_length=10, blank=False)
    
class RtvStatusID(models.Model):
    rtv_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    rtv_status_name = models.CharField(max_length=50, blank=False)
    rtv_status_status = models.CharField(max_length=10, blank=False)
    
class MevStatusID(models.Model):
    mev_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    mev_status_name = models.CharField(max_length=50, blank=False)
    mev_status_status = models.CharField(max_length=10, blank=False)
    
class AtticStatusID(models.Model):
    attic_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    attic_status_name = models.CharField(max_length=50, blank=False)
    attic_status_status = models.CharField(max_length=10, blank=False)
    
class DraughtProofingStatusID(models.Model):
    draught_proofing_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    draught_proofing_status_name = models.CharField(max_length=50, blank=False)
    draught_proofing_status_status = models.CharField(max_length=10, blank=False)
    
class GniStages(models.Model):
    gni_stage_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    gni_stage_name = models.CharField(max_length= 50, unique=True, blank=False, null=False)

class EsbStages(models.Model):
    esb_stage_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    esb_stage_name = models.CharField(max_length= 50, unique=True, blank=False, null=False)
    
class CompanyProjectStages(models.Model):
    project_stage_id = models.AutoField(primary_key=True)
    project_stage_name = models.CharField(max_length= 50, unique=True, blank=False, null=False, db_index=True)
   
class QcStages(models.Model):
    qc_stage_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    qc_stage_name = models.CharField(max_length= 50, unique=True, blank=False, null=False)    
    
class ProjectManagers(models.Model):
    project_manager = models.CharField(max_length= 50, unique=True, blank=False, null=False)