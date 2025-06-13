from django.db import models
from datetime import datetime
# from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
class ProjectDetails(models.Model):
    project_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    project_number = models.CharField(max_length=20, unique=False, blank=False)
    project_name = models.CharField(max_length=100, blank=False)
    project_office = models.CharField(max_length=20 , blank=False, unique=False, default='N/A')
    project_stage = models.CharField(max_length=50, blank=False)
    QC_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    WINDOW_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    CWI_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    OIL_BOILER_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    OIL_TANK_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    EWI_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    PLUMBING_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    IWI_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A') 
    AIRTIGHTNESS_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    RTV_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    MEV_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    ATTIC_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    DRAUGHTPROOFING_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    SOLAR_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    FLOOR_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    MVHR_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    DCV_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    CO_INVOICES_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    FINAL_BER_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    DOW_STATUS = models.CharField(max_length=50, blank=False, unique=False, default='N/A')
    Project_Manager = models.CharField(max_length=50, blank=False, unique=False, null=True, default='N/A')
    

class WindowStatusID(models.Model):
    window_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    window_status_name = models.CharField(max_length=50, blank=False)
    
class CwiStatusID(models.Model):
    cwi_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    cwi_status_name = models.CharField(max_length=50, blank=False)

class OilBoilerStatusID(models.Model):
    oil_boiler_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    oil_boiler_status_name = models.CharField(max_length=50, blank=False)
    
class OilTankStatusID(models.Model):
    oil_tank_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    oil_tank_status_name = models.CharField(max_length=50, blank=False)

class EwiStatusID(models.Model):
    ewi_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    ewi_status_name = models.CharField(max_length=50, blank=False)
    
class PlumbingStatusID(models.Model):
    plumbing_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    plumbing_status_name = models.CharField(max_length=50, blank=False)
    
class IwiStatusID(models.Model):
    iwi_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    iwi_status_name = models.CharField(max_length=50, blank=False)
    
class AirtightnessStatusID(models.Model):
    airtightness_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    airtightness_status_name = models.CharField(max_length=50, blank=False)   
    
class RtvStatusID(models.Model):
    rtv_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    rtv_status_name = models.CharField(max_length=50, blank=False)
    
class MevStatusID(models.Model):
    mev_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    mev_status_name = models.CharField(max_length=50, blank=False)
    
class AtticStatusID(models.Model):
    attic_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    attic_status_name = models.CharField(max_length=50, blank=False)
    
class DraughtProofingStatusID(models.Model):
    draught_proofing_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    draught_proofing_status_name = models.CharField(max_length=50, blank=False)
      
class CompanyProjectStages(models.Model):
    project_stage_id = models.AutoField(primary_key=True)
    project_stage_name = models.CharField(max_length= 50, unique=True, blank=False, null=False, db_index=True)
   
class QcStages(models.Model):
    qc_stage_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    qc_stage_name = models.CharField(max_length= 50, unique=True, blank=False, null=False)    

class SolarStatusID(models.Model):
    solar_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    solar_status_name = models.CharField(max_length=50, blank=False)

class FloorStatusID(models.Model):
    floor_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    floor_status_name = models.CharField(max_length=50, blank=False)

class MVHRStatusID(models.Model):
    mvhr_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    mvhr_status_name = models.CharField(max_length=50, blank=False)

class DCVStatusID(models.Model):
    dcv_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    dcv_status_name = models.CharField(max_length=50, blank=False)

class CoInvoicesStatusID(models.Model):
    co_invoices_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    co_invoices_status_name = models.CharField(max_length=50, blank=False)

class FinalBerStatusID(models.Model):
    final_ber_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    final_ber_status_name = models.CharField(max_length=50, blank=False)

class DowStatusID(models.Model):
    dow_status_id = models.CharField(max_length=20, unique=True, primary_key=True, blank=False)
    dow_status_name = models.CharField(max_length=50, blank=False)
    
class ProjectManagers(models.Model):
    project_manager = models.CharField(max_length= 50, unique=True, blank=False, null=False)

class ProjectOffices(models.Model):
    project_offices = models.CharField(max_length= 50, unique=True, blank=False, null=False)