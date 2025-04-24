from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import requests
from .models import *
from apscheduler.schedulers.background import BackgroundScheduler
import openpyxl
from django.http import HttpResponse

######################################################################################################
# Procore api connection functions for getting data from Procore and storing it in the database
######################################################################################################

# Procore Live credentials
OAUTH_URL = 'https://login.procore.com'
BASE_URL = 'https://api.procore.com'
CLIENT_ID = '78226445873eeed7ac57715df48830f52b6ce6a2fba1c31099a8afd67e26a5d6'
CLIENT_SECRET = 'c46408666b71806645b0d686281c64148b68dec8fd07980815d357d756d87710'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Procore Monthly sandbox credentials
# OAUTH_URL = 'https://login-sandbox-monthly.procore.com'
# BASE_URL = 'https://api-monthly.procore.com'
# CLIENT_ID = '78226445873eeed7ac57715df48830f52b6ce6a2fba1c31099a8afd67e26a5d6'
# CLIENT_SECRET = 'c46408666b71806645b0d686281c64148b68dec8fd07980815d357d756d87710'
# REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Procore sandbox credentials
# OAUTH_URL = 'https://login-sandbox.procore.com'
# BASE_URL = 'https://sandbox.procore.com'
# REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
# CLIENT_ID = 'e6194919d35cdde9440065c0d95468b058a273a51f2ecf6ac99b60b283bc7c01'
# CLIENT_SECRET = 'b98e1bc22386a63ac3e0ff5c4cb569c39256314c0efe1a1554418d804b9ff48b'

######################################################################################################
# Functions for getting credentials from Procore
######################################################################################################
# function to get fresh access token from Procore whenever needed

def get_acess_token():
    '''
    function to get the access token from Procore for 'client credentials' Auth type.
    '''
    post_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(OAUTH_URL+"/oauth/token", data=post_data)
    response_json = response.json()
    # created_at = response_json['created_at']
    # expires_in = response_json['expires_in']
    access_token = response_json['access_token']
    # print(access_token)
    return access_token

# Function to get our company id based on access token whenever needed
def get_company_id():
    '''
    function to get the company id from Procore for API requests. 
    '''
    access_token = get_acess_token()
    url = BASE_URL + "/rest/v1.0/companies"
    headers = {
        "Authorization": "Bearer " + access_token
    }
    response = requests.get(url, headers=headers)
    response_json = response.json()
    # print(response_json)
    company_id = response_json[0]['id']
    return company_id

# Get all WHS projects based on access token and company id and save to database
# GNI = 'custom_field_64774'
# ESB = 'custom_field_64772'

#####################################################################################################
# Functions to run on regular intervals for keeping database uptodate with procore
#####################################################################################################

#Run once a day: Get all current active WHS projects and save to database
def get_all_active_whs_projects():
    '''
    Get all the WHS projects in the Procore and save to the database.
    '''
    access_token = get_acess_token()
    company_id = get_company_id()
    page = 0
    boolean = True
    count = 0
    
    while boolean == True:
        url = BASE_URL + '/rest/v1.1/projects?company_id='+str(company_id)+'&page='+str(page)+'&per_page=20'
        headers = {
            "Authorization": "Bearer " + access_token
        }
        response = requests.get(url, headers=headers)
        response_json = response.json()
        # print(response_json)
        # print(len(response_json))
        if len(response_json) > 0:
            
            for item in response_json:
                project = ProjectDetails()
                # print(item['project_id'])
                
                if item['project_number'] != None and len(item['project_number']) >= 8:
                    striped_project_nmumber = item['project_number'].strip()
                    # print(striped_project_nmumber)
                    
                    if striped_project_nmumber[0] == 'W' and striped_project_nmumber[1] == 'H' and item['project_stage']['name'] != 'WHS 110 - Closed & Paid' and item['project_stage']['name'] != 'WHS 125 - Cancelled':
                        count+=1
                        # print(striped_project_nmumber)
                        project_id = item['id']
                        project.project_id = project_id
                        project.project_number = striped_project_nmumber
                        project.project_name = item['name']
                        project.project_office = 'WHS'
                        stage = item['project_stage']['name']
                        project.project_stage = stage
                        
                        if item['custom_fields']['custom_field_64774']['value'] != None:
                            gni_stage = item['custom_fields']['custom_field_64774']['value']['label']
                            project.GNI_STATUS = gni_stage
                        # else:
                        #     project.GNI_STATUS = 'N/A'
                        if item['custom_fields']['custom_field_64772']['value'] != None:
                            esb_stage = item['custom_fields']['custom_field_64772']['value']['label']
                            project.ESB_STATUS = esb_stage
                        # else:
                        #     project.ESB_STATUS = 'N/A'
                        if item['custom_fields']['custom_field_67252']['value'] != None:
                            qc_stage = item['custom_fields']['custom_field_67252']['value']['label']
                            project.QC_STATUS = qc_stage
                        
                        project_manager = get_project_manager_for_project(project_id)
                        project.Project_Manager = project_manager
                        project.save()
        else:
            boolean = False
            break
        page+=1        
    print('Projects updated successfully')
    return

def get_project_manager_for_project(project_id):
    '''Get project manager'''
    access_token = get_acess_token()
    company_id = get_company_id()
    url = BASE_URL + '/rest/v1.0/project_roles'
    headers = {
        "Authorization": "Bearer " + access_token,
        "Procore-Company-Id": str(company_id)
    }
    payload = {
        'project_id' : project_id,
    }
    response = requests.get(url, headers = headers, json = payload)
    response_json = response.json()
    # print(response_json)   
    if len(response_json) > 0:
        for item in response_json:
            if item["role"] == 'Project Manager':
                project_manager_raw, ignore = item["name"].split("(")
                project_manager = project_manager_raw.strip()
                # print(project_manager)
                pms_in_db = ProjectManagers.objects.values_list('project_manager', flat=True)
                pms_in_db_list = list(pms_in_db)
                # print(pms_in_db_list)
                if project_manager not in pms_in_db_list:
                    projectManager = ProjectManagers()
                    projectManager.project_manager = project_manager
                    projectManager.save()
                return project_manager
    else:
        project_manager = "N/A"
        return project_manager

# GNI = 'custom_field_64774'
# ESB = 'custom_field_64772'
# QC_Mid_Final = 'custom_field_67252'

# Function for getting the statuses of the custom fields lov entries from Procore and save to DB   
def get_lov_entries_statuses():
    '''
    Function gets statuses for the lov entries custom fields with status id's and saves them to DB
    '''
    DICT_OF_CUSTOM_FILEDS = {
        'GNI' : 64774,
        'ESB' : 64772,
        'QC_Mid_final' : 67252,
    }
    for val in DICT_OF_CUSTOM_FILEDS.values():
        access_token = get_acess_token()
        company_id = get_company_id()
        url = BASE_URL + '/rest/v1.0/custom_field_definitions/'+str(val)+'/custom_field_lov_entries'
        headers = {
            "Authorization": "Bearer " + access_token,
            'Procore-Company-Id': str(company_id)
        }
        payload = {
            'company_id' : str(company_id), 
        }
        response = requests.get(url, headers=headers, json=payload)    
        response_json = response.json()
        # print(response_json)   
        if val == 64774:
            for item in response_json:
                gni_stage = GniStages()
                gni_stage.gni_stage_id = item['id']
                gni_stage.gni_stage_name = item['label']
                gni_stage.save()  
        elif val == 64772:
            for item in response_json:
                esb_stage = EsbStages()
                esb_stage.esb_stage_id = item['id']
                esb_stage.esb_stage_name = item['label']
                esb_stage.save()
        elif val == 67252:
            for item in response_json:
                qc_stage = QcStages()
                qc_stage.qc_stage_id = item['id']
                qc_stage.qc_stage_name = item['label']
                qc_stage.save()
    return

#Run once a day: function saves all the company level WHS stages in the DB wit their id
def save_company_stages():
    access_token = get_acess_token()
    company_id = str(get_company_id())
    url = BASE_URL + "/rest/v1.0/companies/"+company_id+"/project_stages"
    headers = {
        "Authorization": "Bearer " + access_token,
        'Procore-Company-Id': company_id
    }
    response = requests.get(url, headers=headers)
    response_json = response.json()
    for val in response_json:
        if val['name'][0] == 'W' and val['name'] != 'WHS 045 - Do Not Use' and val['name'] != 'WHS 047 - Do Not Use':
            project_object = CompanyProjectStages()
            project_object.project_stage_id = val['id']
            project_object.project_stage_name = val['name']
            project_object.save()
    return 

# print(save_company_stages())

DICT_OF_CORRESPONDENCES = {
   'ATT PO' : 562949953457930, 'ATTIC PO' : 562949953443421,
   'CWI PO' : 562949953457927, 'DP PO' : 562949953446405,
   'EWI PO' : 562949953457926, 'IWI PO' : 562949953457929,
   'MEV PO' : 562949953457931, 'OBM PO' : 562949953487254,
   'OTM PO' : 562949953443411, 'PLUMB PO' : 562949953457928,
   'RV PO' : 562949953487253, 'WIN PO' : 562949953443417
}

#Runs only once at start: This function gets all the generic tool items/correspondences in the company level and saves required ones to db
def get_all_generic_tools():
    access_token = get_acess_token()
    company_id = str(get_company_id())
    url = BASE_URL + "/rest/v1.0/companies/"+company_id+"/generic_tools"
    headers = {
        "Authorization": "Bearer " + access_token,
        'Procore-Company-Id': company_id
    }
    response = requests.get(url, headers=headers)
    response_json = response.json()
    list_of_correspondences = response_json
    for correspondence in list_of_correspondences:
        if correspondence["id"] in DICT_OF_CORRESPONDENCES.values():
            correspondence_type_id = CorrespondenceTypeID()
            correspondence_type_id.correspondence_id = correspondence['id']
            correspondence_type_id.correspondence_name = correspondence['configurable_field_sets'][0]['name']
            correspondence_type_id.correspondence_abbreviation = correspondence['abbreviation']
            correspondence_type_id.save()
    return

# get_all_generic_tools()

#Runs once a day: Function to get all the statuses of required correspondences with their id's
def get_generic_tool_statuses():
    '''
    This function gets all the statuses from Procore for required correspondences with their id's
    and save in the database
    '''
    access_token = get_acess_token()
    company_id = str(get_company_id())
    generic_tool_ids = DICT_OF_CORRESPONDENCES.values()
    # print(generic_tool_ids)
    for generic_tool_id in generic_tool_ids:
        url = BASE_URL + "/rest/v1.0/companies/"+company_id+"/generic_tools/"+str(generic_tool_id)+"/statuses"
        headers = {
            "Authorization": "Bearer " + access_token,
            'Procore-Company-Id': company_id
        }
        response = requests.get(url, headers=headers)
        response_json = response.json()
        # print(response_json)
        if generic_tool_id == 562949953457930:
            for status in response_json:
                airtightness_status_id = AirtightnessStatusID()
                airtightness_status_id.airtightness_status_id = status['id']
                airtightness_status_id.airtightness_status_status = status['status']
                airtightness_status_id.airtightness_status_name = status['status_name']
                airtightness_status_id.save()
        elif generic_tool_id == 562949953443421:
            for status in response_json:
                attic_status_id = AtticStatusID()
                attic_status_id.attic_status_id = status['id']
                attic_status_id.attic_status_status = status['status']
                attic_status_id.attic_status_name = status['status_name']
                attic_status_id.save()
        elif generic_tool_id == 562949953457927:
            for status in response_json:
                cwi_status_id = CwiStatusID()
                cwi_status_id.cwi_status_id = status['id']
                cwi_status_id.cwi_status_status = status['status']
                cwi_status_id.cwi_status_name = status['status_name']
                cwi_status_id.save()
        elif generic_tool_id == 562949953446405:
            for status in response_json:
                draughtproofing_status_id = DraughtProofingStatusID()
                draughtproofing_status_id.draught_proofing_status_id = status['id']
                draughtproofing_status_id.draught_proofing_status_status = status['status']
                draughtproofing_status_id.draught_proofing_status_name = status['status_name']
                draughtproofing_status_id.save()
        elif generic_tool_id == 562949953457926:
            for status in response_json:
                ewi_status_id = EwiStatusID()
                ewi_status_id.ewi_status_id = status['id']
                ewi_status_id.ewi_status_status = status['status']
                ewi_status_id.ewi_status_name = status['status_name']
                ewi_status_id.save()
        elif generic_tool_id == 562949953457929:
            for status in response_json:
                iwi_status_id = IwiStatusID()
                iwi_status_id.iwi_status_id = status['id']
                iwi_status_id.iwi_status_status = status['status']
                iwi_status_id.iwi_status_name = status['status_name']
                iwi_status_id.save()
        elif generic_tool_id == 562949953457931:
            for status in response_json:
                mev_status_id = MevStatusID()
                mev_status_id.mev_status_id = status['id']
                mev_status_id.mev_status_status = status['status']
                mev_status_id.mev_status_name = status['status_name']
                mev_status_id.save()
        elif generic_tool_id == 562949953487254:
            for status in response_json:
                oil_boiler_status_id = OilBoilerStatusID()
                oil_boiler_status_id.oil_boiler_status_id = status['id']
                oil_boiler_status_id.oil_boiler_status_status = status['status']
                oil_boiler_status_id.oil_boiler_status_name = status['status_name']
                oil_boiler_status_id.save()
        elif generic_tool_id == 562949953443411:
            for status in response_json:
                oil_tank_status_id = OilTankStatusID()
                oil_tank_status_id.oil_tank_status_id = status['id']
                oil_tank_status_id.oil_tank_status_status = status['status']
                oil_tank_status_id.oil_tank_status_name = status['status_name']
                oil_tank_status_id.save()
        elif generic_tool_id == 562949953457928:
            for status in response_json:
                plumbing_status_id = PlumbingStatusID()
                plumbing_status_id.plumbing_status_id = status['id']
                plumbing_status_id.plumbing_status_status = status['status']
                plumbing_status_id.plumbing_status_name = status['status_name']
                plumbing_status_id.save()
        elif generic_tool_id == 562949953487253:
            for status in response_json:
                rtv_status_id = RtvStatusID()
                rtv_status_id.rtv_status_id = status['id']
                rtv_status_id.rtv_status_status = status['status']
                rtv_status_id.rtv_status_name = status['status_name']
                rtv_status_id.save()
        elif generic_tool_id == 562949953443417:
            for status in response_json:
                window_status_id = WindowStatusID()
                window_status_id.window_status_id = status['id']
                window_status_id.window_status_status = status['status']
                window_status_id.window_status_name = status['status_name']
                window_status_id.save()
    return

# print(get_generic_tool_statuses())

# This function gets all the current statuses of required correspondences for all the projects in database
# and saves them in database
# Runs every 60 seconds
def get_all_correspondences_for_the_project():
    '''
    This function gets all the current statuses of required correspondences for all the projects in database 
    and saves them in database
    '''
    access_token = get_acess_token()
    company_id = get_company_id()
    project_ids = ProjectDetails.objects.values_list('project_id', flat=True)
    for project_id in project_ids:
        # print(project_id)
        url = BASE_URL + '/rest/v1.0/projects/'+str(project_id)+'/correspondence_type_items'
        headers = {
            "Authorization": "Bearer " + access_token,
            'Procore-Company-Id': str(company_id)
        }
        response = requests.get(url, headers=headers)
        response_json = response.json()
        # print(response_json)
        if type(response_json) == list: 
            for item in response_json:
                # print(item)
                # if item['generic_tool']['abbreviation'] in DICT_OF_CORRESPONDENCES.keys():
                project = ProjectDetails.objects.get(project_id=project_id)
    
                if item['generic_tool']['id'] in DICT_OF_CORRESPONDENCES.values():
                
                    if item['generic_tool']['id'] == 562949953457930: 
                        project.AIRTIGHTNESS_STATUS = item['status']
                        project.airtightness_correspondence_id = item['id']
                    # else:
                    #     project.AIRTIGHTNESS_STATUS = 'N/A'
                    
                    if item['generic_tool']['id'] == 562949953443421: 
                        project.ATTIC_STATUS = item['status']
                        project.attic_correspondence_id = item['id']
                    # else:
                    #     project.ATTIC_STATUS = 'N/A'
                    
                    if item['generic_tool']['id'] == 562949953457927: 
                        project.CWI_STATUS = item['status']
                        project.cwi_correpondence_id = item['id']
                    # else:
                    #     project.CWI_STATUS = 'N/A'
                    
                    if item['generic_tool']['id'] == 562949953446405: 
                        project.DRAUGHTPROOFING_STATUS = item['status']
                        project.draughtproofing_correspondence_id = item['id'] 
                    # else:
                    #     project.DRAUGHTPROOFING_STATUS = 'N/A'  
                    
                    if item['generic_tool']['id'] == 562949953457926: 
                        project.EWI_STATUS = item['status'] 
                        project.ewi_correspondence_id = item['id']
                    # else:
                    #     project.EWI_STATUS = 'N/A' 
                    
                    if item['generic_tool']['id'] == 562949953457929: 
                        project.IWI_STATUS = item['status'] 
                        project.iwi_correspondence_id = item['id']
                    # else:
                    #     project.IWI_STATUS = 'N/A'  
                    
                    if item['generic_tool']['id'] == 562949953457931: 
                        project.MEV_STATUS = item['status'] 
                        project.mev_correspondence_id = item['id']
                    # else:
                        # project.MEV_STATUS = 'N/A'
                    
                    if item['generic_tool']['id'] == 562949953487254: 
                        project.OIL_BOILER_STATUS = item['status']
                        project.oil_boiler_correspondence_id = item['id']  
                    # else:
                        # project.OIL_BOILER_STATUS = 'N/A'  
                    
                    if item['generic_tool']['id'] == 562949953443411: 
                        project.OIL_TANK_STATUS = item['status'] 
                        project.oil_tank_correspondence_id = item['id'] 
                    # else:
                        # project.OIL_TANK_STATUS = 'N/A'
                    
                    if item['generic_tool']['id'] == 562949953457928: 
                        project.PLUMBING_STATUS = item['status'] 
                        project.plumbing_correpondence_id = item['id']
                    # else:
                        # project.PLUMBING_STATUS = 'N/A' 
                    
                    if item['generic_tool']['id'] == 562949953487253: 
                        project.RTV_STATUS = item['status'] 
                        project.rtv_correspondence_id = item['id']
                    # else:
                        # project.RTV_STATUS = 'N/A'
                        
                    if item['generic_tool']['id'] == 562949953443417: 
                        project.WINDOW_STATUS = item['status']
                        project.window_correspondence_id = item['id']
                    # else:
                        # project.WINDOW_STATUS = 'N/A' 
                    project.save()
    print('Correspondences statuses updated')
    return 

def clean_db_for_fresh_projects():
    a = ProjectDetails.objects.all()
    a.delete()
    return

def clean_db_for_fresh_statuses():
    a = WindowStatusID.objects.all()
    a.delete()
    b = CwiStatusID.objects.all()
    b.delete()
    c = OilBoilerStatusID.objects.all()
    c.delete()
    d = OilTankStatusID.objects.all()
    d.delete()
    e = EwiStatusID.objects.all()
    e.delete()
    f = PlumbingStatusID.objects.all()
    f.delete()
    g = IwiStatusID.objects.all()
    g.delete()
    h = AirtightnessStatusID.objects.all()
    h.delete()
    i = RtvStatusID.objects.all()
    i.delete()
    j = MevStatusID.objects.all()
    j.delete()
    k = AtticStatusID.objects.all()
    k.delete()
    l = DraughtProofingStatusID.objects.all()
    l.delete()
    m = GniStages.objects.all()
    m.delete()
    n = EsbStages.objects.all()
    n.delete()
    o = CompanyProjectStages.objects.all()
    o.delete()
     
    z = CorrespondenceTypeID.objects.all()
    z.delete()
    return

########################################################################################################  
# create your views here
########################################################################################################

@login_required(login_url='/accounts/login/')
def dashboard(request):
    if request.method == 'GET':
        projects_for_paging = ProjectDetails.objects.all().order_by('project_name')
        total_project_in_db = projects_for_paging.count()
    airtightness_options = AirtightnessStatusID.objects.all()
    attic_options = AtticStatusID.objects.all()
    cwi_options = CwiStatusID.objects.all()
    draught_proofing_options = DraughtProofingStatusID.objects.all()
    ewi_options = EwiStatusID.objects.all()
    iwi_options = IwiStatusID.objects.all()
    mev_options = MevStatusID.objects.all()
    oil_boiler_options = OilBoilerStatusID.objects.all()
    oil_tank_options = OilTankStatusID.objects.all()
    plumbing_options = PlumbingStatusID.objects.all()
    rtv_options = RtvStatusID.objects.all()
    window_options = WindowStatusID.objects.all()
    stages_options = CompanyProjectStages.objects.all().order_by('project_stage_name')
    gni_options = GniStages.objects.all()
    esb_options = EsbStages.objects.all()
    qc_options = QcStages.objects.all()
    pm_options = ProjectManagers.objects.all()
    if request.method == 'POST':
        if 'stage' in request.POST:
            split_str_list = request.POST['stage'].split("_")
            main_stage_name = split_str_list[0]
            project_id = split_str_list[1]  
            response_status_code = update_procore_project_stage(project_id, main_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.project_stage = main_stage_name
                project_object.save()
        if 'gni' in request.POST:
            split_str_list = request.POST['gni'].split("_")
            gni_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            esb_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.GNI_STATUS = gni_stage_name
                project_object.save()
        if 'esb' in request.POST:
            split_str_list = request.POST['esb'].split("_")
            esb_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.ESB_STATUS = esb_stage_name
                project_object.save()
        if 'qc_mid_final' in request.POST:
            split_str_list = request.POST['qc_mid_final'].split("_")
            qc_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            esb_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.QC_STATUS = qc_stage_name
                project_object.save()
        if 'window' in request.POST:
            split_str_list = request.POST['window'].split("_")
            window_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.window_correspondence_id != 0:
                generic_tool_item_id = project_object.window_correspondence_id
                project_object.WINDOW_STATUS = window_stage_name
                project_object.save()
                abbrevation = 'WIN PO'
                update_procore_correspondence(project_id, abbrevation, window_stage_name, generic_tool_item_id)
        if 'cwi' in request.POST:
            split_str_list = request.POST['cwi'].split("_")
            cwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.cwi_correpondence_id != 0:
                generic_tool_item_id = project_object.cwi_correpondence_id
                project_object.CWI_STATUS = cwi_stage_name
                project_object.save()
                abbrevation = 'CWI PO'
                update_procore_correspondence(project_id, abbrevation, cwi_stage_name, generic_tool_item_id)
        if 'oil_boiler' in request.POST:
            split_str_list = request.POST['oil_boiler'].split("_")
            oil_boiler_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_boiler_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_boiler_correspondence_id
                project_object.OIL_BOILER_STATUS = oil_boiler_stage_name
                project_object.save()
                abbrevation = 'OBM PO'
                update_procore_correspondence(project_id, abbrevation, oil_boiler_stage_name, generic_tool_item_id)
        if 'oil_tank' in request.POST:
            split_str_list = request.POST['oil_tank'].split("_")
            oil_tank_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_tank_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_tank_correspondence_id
                project_object.OIL_TANK_STATUS = oil_tank_stage_name
                project_object.save()
                abbrevation = 'OTM PO'
                update_procore_correspondence(project_id, abbrevation, oil_tank_stage_name, generic_tool_item_id)
        if 'ewi' in request.POST:
            split_str_list = request.POST['ewi'].split("_")
            ewi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.ewi_correspondence_id != 0:
                generic_tool_item_id = project_object.ewi_correspondence_id
                project_object.EWI_STATUS = ewi_stage_name
                project_object.save()
                abbrevation = 'EWI PO'
                update_procore_correspondence(project_id, abbrevation, ewi_stage_name, generic_tool_item_id)
        if 'plumbing' in request.POST:
            split_str_list = request.POST['plumbing'].split("_")
            plumbing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.plumbing_correpondence_id != 0:
                generic_tool_item_id = project_object.plumbing_correpondence_id
                project_object.PLUMBING_STATUS = plumbing_stage_name
                project_object.save()
                abbrevation = 'PLUMB PO'
                update_procore_correspondence(project_id, abbrevation, plumbing_stage_name, generic_tool_item_id)
        if 'iwi' in request.POST:
            split_str_list = request.POST['iwi'].split("_")
            iwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.iwi_correspondence_id != 0:
                generic_tool_item_id = project_object.iwi_correspondence_id
                project_object.IWI_STATUS = iwi_stage_name
                project_object.save()
                abbrevation = 'IWI PO'
                update_procore_correspondence(project_id, abbrevation, iwi_stage_name, generic_tool_item_id)
        if 'airtightness' in request.POST:
            split_str_list = request.POST['airtightness'].split("_")
            airtightness_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.airtightness_correspondence_id != 0:
                generic_tool_item_id = project_object.airtightness_correspondence_id
                project_object.AIRTIGHTNESS_STATUS = airtightness_stage_name
                project_object.save()
                abbrevation = 'ATT PO'
                update_procore_correspondence(project_id, abbrevation, airtightness_stage_name, generic_tool_item_id)
        if 'rtv' in request.POST:
            split_str_list = request.POST['rtv'].split("_")
            rtv_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.rtv_correspondence_id != 0:
                generic_tool_item_id = project_object.rtv_correspondence_id
                project_object.RTV_STATUS = rtv_stage_name
                project_object.save()
                abbrevation = 'RV PO'
                update_procore_correspondence(project_id, abbrevation, rtv_stage_name, generic_tool_item_id)
        if 'mev' in request.POST:
            split_str_list = request.POST['mev'].split("_")
            mev_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.mev_correspondence_id != 0:
                generic_tool_item_id = project_object.mev_correspondence_id
                project_object.MEV_STATUS = mev_stage_name
                project_object.save()
                abbrevation = 'MEV PO'
                update_procore_correspondence(project_id, abbrevation, mev_stage_name, generic_tool_item_id)
        if 'attic' in request.POST:
            split_str_list = request.POST['attic'].split("_")
            attic_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.attic_correspondence_id != 0:
                generic_tool_item_id = project_object.attic_correspondence_id
                project_object.ATTIC_STATUS = attic_stage_name
                project_object.save()
                abbrevation = 'ATTIC PO'
                update_procore_correspondence(project_id, abbrevation, attic_stage_name, generic_tool_item_id)
        if 'draughtproofing' in request.POST:
            split_str_list = request.POST['draughtproofing'].split("_")
            draughtproofing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.draughtproofing_correspondence_id != 0:
                generic_tool_item_id = project_object.draughtproofing_correspondence_id
                project_object.DRAUGHTPROOFING_STATUS = draughtproofing_stage_name
                project_object.save()
                abbrevation = 'DP PO'
                update_procore_correspondence(project_id, abbrevation, draughtproofing_stage_name, generic_tool_item_id)
        print(split_str_list)
        projects_for_paging = ProjectDetails.objects.all().order_by('project_name')
        total_project_in_db = projects_for_paging.count()
        
    paginator = Paginator(projects_for_paging, per_page=10, orphans=3)
    page = request.GET.get('page') # get the page number from the URL
    page_object = paginator.get_page(page)
    return render(request, 'home.html', context= {"projects" : page_object, 'airtightness_options' : airtightness_options, 'attic_options' : attic_options,
        'cwi_options' : cwi_options, 'draught_proofing_options' : draught_proofing_options, 'ewi_options' : ewi_options,
        'iwi_options' : iwi_options, 'mev_options' : mev_options, 'oil_boiler_options' : oil_boiler_options, 'pm_options' : pm_options,
        'oil_tank_options' : oil_tank_options, 'plumbing_options' : plumbing_options, 'rtv_options' : rtv_options, 'qc_options' : qc_options, 
        'window_options' : window_options, 'stages_options' : stages_options, 'gni_options' : gni_options, 'esb_options' : esb_options, 
        'total_project_in_db' : total_project_in_db, 'page_object':page_object})


@login_required(login_url='/accounts/login/')
def filter_projects_by_stage(request):
    if 'filter-by-stage' in request.POST:
        filter_stage = request.POST['filter-by-stage'] 
        request.session['filter-by-stage'] = filter_stage
    elif request.session.get('filter-by-stage'):
        filter_stage = request.session.get('filter-by-stage')
    else:
        redirect(dashboard)
    # print(filter_stage)
    filtered_projects = ProjectDetails.objects.filter(project_stage=str(filter_stage)).values().order_by('project_name')
    filtered_projects_count = filtered_projects.count()
    airtightness_options = AirtightnessStatusID.objects.all()
    attic_options = AtticStatusID.objects.all()
    cwi_options = CwiStatusID.objects.all()
    draught_proofing_options = DraughtProofingStatusID.objects.all()
    ewi_options = EwiStatusID.objects.all()
    iwi_options = IwiStatusID.objects.all()
    mev_options = MevStatusID.objects.all()
    oil_boiler_options = OilBoilerStatusID.objects.all()
    oil_tank_options = OilTankStatusID.objects.all()
    plumbing_options = PlumbingStatusID.objects.all()
    rtv_options = RtvStatusID.objects.all()
    window_options = WindowStatusID.objects.all()
    stages_options = CompanyProjectStages.objects.all().order_by('project_stage_name')
    gni_options = GniStages.objects.all()
    esb_options = EsbStages.objects.all()
    qc_options = QcStages.objects.all()
    pm_options = ProjectManagers.objects.all()
    if request.method == 'POST':
        if 'stage' in request.POST:
            split_str_list = request.POST['stage'].split("_")
            main_stage_name = split_str_list[0]
            project_id = split_str_list[1]  
            response_status_code = update_procore_project_stage(project_id, main_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.project_stage = main_stage_name
                project_object.save()
        if 'gni' in request.POST:
            split_str_list = request.POST['gni'].split("_")
            gni_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            esb_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.GNI_STATUS = gni_stage_name
                project_object.save()
        if 'esb' in request.POST:
            split_str_list = request.POST['esb'].split("_")
            esb_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.ESB_STATUS = esb_stage_name
                project_object.save()
        if 'qc_mid_final' in request.POST:
            split_str_list = request.POST['qc_mid_final'].split("_")
            qc_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            esb_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.QC_STATUS = qc_stage_name
                project_object.save()
        if 'window' in request.POST:
            split_str_list = request.POST['window'].split("_")
            window_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.window_correspondence_id != 0:
                generic_tool_item_id = project_object.window_correspondence_id
                project_object.WINDOW_STATUS = window_stage_name
                project_object.save()
                abbrevation = 'WIN PO'
                update_procore_correspondence(project_id, abbrevation, window_stage_name, generic_tool_item_id)
        if 'cwi' in request.POST:
            split_str_list = request.POST['cwi'].split("_")
            cwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.cwi_correpondence_id != 0:
                generic_tool_item_id = project_object.cwi_correpondence_id
                project_object.CWI_STATUS = cwi_stage_name
                project_object.save()
                abbrevation = 'CWI PO'
                update_procore_correspondence(project_id, abbrevation, cwi_stage_name, generic_tool_item_id)
        if 'oil_boiler' in request.POST:
            split_str_list = request.POST['oil_boiler'].split("_")
            oil_boiler_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_boiler_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_boiler_correspondence_id
                project_object.OIL_BOILER_STATUS = oil_boiler_stage_name
                project_object.save()
                abbrevation = 'OBM PO'
                update_procore_correspondence(project_id, abbrevation, oil_boiler_stage_name, generic_tool_item_id)
        if 'oil_tank' in request.POST:
            split_str_list = request.POST['oil_tank'].split("_")
            oil_tank_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_tank_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_tank_correspondence_id
                project_object.OIL_TANK_STATUS = oil_tank_stage_name
                project_object.save()
                abbrevation = 'OTM PO'
                update_procore_correspondence(project_id, abbrevation, oil_tank_stage_name, generic_tool_item_id)
        if 'ewi' in request.POST:
            split_str_list = request.POST['ewi'].split("_")
            ewi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.ewi_correspondence_id != 0:
                generic_tool_item_id = project_object.ewi_correspondence_id
                project_object.EWI_STATUS = ewi_stage_name
                project_object.save()
                abbrevation = 'EWI PO'
                update_procore_correspondence(project_id, abbrevation, ewi_stage_name, generic_tool_item_id)
        if 'plumbing' in request.POST:
            split_str_list = request.POST['plumbing'].split("_")
            plumbing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.plumbing_correpondence_id != 0:
                generic_tool_item_id = project_object.plumbing_correpondence_id
                project_object.PLUMBING_STATUS = plumbing_stage_name
                project_object.save()
                abbrevation = 'PLUMB PO'
                update_procore_correspondence(project_id, abbrevation, plumbing_stage_name, generic_tool_item_id)
        if 'iwi' in request.POST:
            split_str_list = request.POST['iwi'].split("_")
            iwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.iwi_correspondence_id != 0:
                generic_tool_item_id = project_object.iwi_correspondence_id
                project_object.IWI_STATUS = iwi_stage_name
                project_object.save()
                abbrevation = 'IWI PO'
                update_procore_correspondence(project_id, abbrevation, iwi_stage_name, generic_tool_item_id)
        if 'airtightness' in request.POST:
            split_str_list = request.POST['airtightness'].split("_")
            airtightness_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.airtightness_correspondence_id != 0:
                generic_tool_item_id = project_object.airtightness_correspondence_id
                project_object.AIRTIGHTNESS_STATUS = airtightness_stage_name
                project_object.save()
                abbrevation = 'ATT PO'
                update_procore_correspondence(project_id, abbrevation, airtightness_stage_name, generic_tool_item_id)
        if 'rtv' in request.POST:
            split_str_list = request.POST['rtv'].split("_")
            rtv_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.rtv_correspondence_id != 0:
                generic_tool_item_id = project_object.rtv_correspondence_id
                project_object.RTV_STATUS = rtv_stage_name
                project_object.save()
                abbrevation = 'RV PO'
                update_procore_correspondence(project_id, abbrevation, rtv_stage_name, generic_tool_item_id)
        if 'mev' in request.POST:
            split_str_list = request.POST['mev'].split("_")
            mev_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.mev_correspondence_id != 0:
                generic_tool_item_id = project_object.mev_correspondence_id
                project_object.MEV_STATUS = mev_stage_name
                project_object.save()
                abbrevation = 'MEV PO'
                update_procore_correspondence(project_id, abbrevation, mev_stage_name, generic_tool_item_id)
        if 'attic' in request.POST:
            split_str_list = request.POST['attic'].split("_")
            attic_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.attic_correspondence_id != 0:
                generic_tool_item_id = project_object.attic_correspondence_id
                project_object.ATTIC_STATUS = attic_stage_name
                project_object.save()
                abbrevation = 'ATTIC PO'
                update_procore_correspondence(project_id, abbrevation, attic_stage_name, generic_tool_item_id)
        if 'draughtproofing' in request.POST:
            split_str_list = request.POST['draughtproofing'].split("_")
            draughtproofing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.draughtproofing_correspondence_id != 0:
                generic_tool_item_id = project_object.draughtproofing_correspondence_id
                project_object.DRAUGHTPROOFING_STATUS = draughtproofing_stage_name
                project_object.save()
                abbrevation = 'DP PO'
                update_procore_correspondence(project_id, abbrevation, draughtproofing_stage_name, generic_tool_item_id)
    
    paginator = Paginator(filtered_projects, per_page=10, orphans=3)
    page = request.GET.get('page') # get the page number from the URL
    page_object = paginator.get_page(page)
    return render(request, 'filtered_projects_by_stage.html', context= {"projects" : page_object, 'airtightness_options' : airtightness_options, 'attic_options' : attic_options,
        'cwi_options' : cwi_options, 'draught_proofing_options' : draught_proofing_options, 'ewi_options' : ewi_options,
        'iwi_options' : iwi_options, 'mev_options' : mev_options, 'oil_boiler_options' : oil_boiler_options, 'pm_options' : pm_options,
        'oil_tank_options' : oil_tank_options, 'plumbing_options' : plumbing_options, 'rtv_options' : rtv_options, 'qc_options' : qc_options,
        'window_options' : window_options, 'stages_options' : stages_options, 'gni_options' : gni_options, 'esb_options' : esb_options, 
        'total_project_in_db' : filtered_projects_count, 'filter_stage' : filter_stage, 'page_object' : page_object})

@login_required(login_url='/accounts/login/')
def filter_projects_by_pm(request):
    if 'filter-by-pm' in request.POST:
        filter_stage = request.POST['filter-by-pm'] 
        request.session['filter-by-pm'] = filter_stage
    elif request.session.get('filter-by-pm'):
        filter_stage = request.session.get('filter-by-pm')
    else:
        redirect(dashboard)
    # print(filter_stage)
    filtered_projects = ProjectDetails.objects.filter(Project_Manager=str(filter_stage)).values().order_by('project_name')
    filtered_projects_count = filtered_projects.count()
    airtightness_options = AirtightnessStatusID.objects.all()
    attic_options = AtticStatusID.objects.all()
    cwi_options = CwiStatusID.objects.all()
    draught_proofing_options = DraughtProofingStatusID.objects.all()
    ewi_options = EwiStatusID.objects.all()
    iwi_options = IwiStatusID.objects.all()
    mev_options = MevStatusID.objects.all()
    oil_boiler_options = OilBoilerStatusID.objects.all()
    oil_tank_options = OilTankStatusID.objects.all()
    plumbing_options = PlumbingStatusID.objects.all()
    rtv_options = RtvStatusID.objects.all()
    window_options = WindowStatusID.objects.all()
    stages_options = CompanyProjectStages.objects.all().order_by('project_stage_name')
    gni_options = GniStages.objects.all()
    esb_options = EsbStages.objects.all()
    qc_options = QcStages.objects.all()
    pm_options = ProjectManagers.objects.all()
    if request.method == 'POST':
        if 'stage' in request.POST:
            split_str_list = request.POST['stage'].split("_")
            main_stage_name = split_str_list[0]
            project_id = split_str_list[1]  
            response_status_code = update_procore_project_stage(project_id, main_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.project_stage = main_stage_name
                project_object.save()
        if 'gni' in request.POST:
            split_str_list = request.POST['gni'].split("_")
            gni_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            esb_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.GNI_STATUS = gni_stage_name
                project_object.save()
        if 'esb' in request.POST:
            split_str_list = request.POST['esb'].split("_")
            esb_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.ESB_STATUS = esb_stage_name
                project_object.save()
        if 'qc_mid_final' in request.POST:
            split_str_list = request.POST['qc_mid_final'].split("_")
            qc_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            esb_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.QC_STATUS = qc_stage_name
                project_object.save()
        if 'window' in request.POST:
            split_str_list = request.POST['window'].split("_")
            window_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.window_correspondence_id != 0:
                generic_tool_item_id = project_object.window_correspondence_id
                project_object.WINDOW_STATUS = window_stage_name
                project_object.save()
                abbrevation = 'WIN PO'
                update_procore_correspondence(project_id, abbrevation, window_stage_name, generic_tool_item_id)
        if 'cwi' in request.POST:
            split_str_list = request.POST['cwi'].split("_")
            cwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.cwi_correpondence_id != 0:
                generic_tool_item_id = project_object.cwi_correpondence_id
                project_object.CWI_STATUS = cwi_stage_name
                project_object.save()
                abbrevation = 'CWI PO'
                update_procore_correspondence(project_id, abbrevation, cwi_stage_name, generic_tool_item_id)
        if 'oil_boiler' in request.POST:
            split_str_list = request.POST['oil_boiler'].split("_")
            oil_boiler_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_boiler_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_boiler_correspondence_id
                project_object.OIL_BOILER_STATUS = oil_boiler_stage_name
                project_object.save()
                abbrevation = 'OBM PO'
                update_procore_correspondence(project_id, abbrevation, oil_boiler_stage_name, generic_tool_item_id)
        if 'oil_tank' in request.POST:
            split_str_list = request.POST['oil_tank'].split("_")
            oil_tank_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_tank_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_tank_correspondence_id
                project_object.OIL_TANK_STATUS = oil_tank_stage_name
                project_object.save()
                abbrevation = 'OTM PO'
                update_procore_correspondence(project_id, abbrevation, oil_tank_stage_name, generic_tool_item_id)
        if 'ewi' in request.POST:
            split_str_list = request.POST['ewi'].split("_")
            ewi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.ewi_correspondence_id != 0:
                generic_tool_item_id = project_object.ewi_correspondence_id
                project_object.EWI_STATUS = ewi_stage_name
                project_object.save()
                abbrevation = 'EWI PO'
                update_procore_correspondence(project_id, abbrevation, ewi_stage_name, generic_tool_item_id)
        if 'plumbing' in request.POST:
            split_str_list = request.POST['plumbing'].split("_")
            plumbing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.plumbing_correpondence_id != 0:
                generic_tool_item_id = project_object.plumbing_correpondence_id
                project_object.PLUMBING_STATUS = plumbing_stage_name
                project_object.save()
                abbrevation = 'PLUMB PO'
                update_procore_correspondence(project_id, abbrevation, plumbing_stage_name, generic_tool_item_id)
        if 'iwi' in request.POST:
            split_str_list = request.POST['iwi'].split("_")
            iwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.iwi_correspondence_id != 0:
                generic_tool_item_id = project_object.iwi_correspondence_id
                project_object.IWI_STATUS = iwi_stage_name
                project_object.save()
                abbrevation = 'IWI PO'
                update_procore_correspondence(project_id, abbrevation, iwi_stage_name, generic_tool_item_id)
        if 'airtightness' in request.POST:
            split_str_list = request.POST['airtightness'].split("_")
            airtightness_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.airtightness_correspondence_id != 0:
                generic_tool_item_id = project_object.airtightness_correspondence_id
                project_object.AIRTIGHTNESS_STATUS = airtightness_stage_name
                project_object.save()
                abbrevation = 'ATT PO'
                update_procore_correspondence(project_id, abbrevation, airtightness_stage_name, generic_tool_item_id)
        if 'rtv' in request.POST:
            split_str_list = request.POST['rtv'].split("_")
            rtv_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.rtv_correspondence_id != 0:
                generic_tool_item_id = project_object.rtv_correspondence_id
                project_object.RTV_STATUS = rtv_stage_name
                project_object.save()
                abbrevation = 'RV PO'
                update_procore_correspondence(project_id, abbrevation, rtv_stage_name, generic_tool_item_id)
        if 'mev' in request.POST:
            split_str_list = request.POST['mev'].split("_")
            mev_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.mev_correspondence_id != 0:
                generic_tool_item_id = project_object.mev_correspondence_id
                project_object.MEV_STATUS = mev_stage_name
                project_object.save()
                abbrevation = 'MEV PO'
                update_procore_correspondence(project_id, abbrevation, mev_stage_name, generic_tool_item_id)
        if 'attic' in request.POST:
            split_str_list = request.POST['attic'].split("_")
            attic_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.attic_correspondence_id != 0:
                generic_tool_item_id = project_object.attic_correspondence_id
                project_object.ATTIC_STATUS = attic_stage_name
                project_object.save()
                abbrevation = 'ATTIC PO'
                update_procore_correspondence(project_id, abbrevation, attic_stage_name, generic_tool_item_id)
        if 'draughtproofing' in request.POST:
            split_str_list = request.POST['draughtproofing'].split("_")
            draughtproofing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.draughtproofing_correspondence_id != 0:
                generic_tool_item_id = project_object.draughtproofing_correspondence_id
                project_object.DRAUGHTPROOFING_STATUS = draughtproofing_stage_name
                project_object.save()
                abbrevation = 'DP PO'
                update_procore_correspondence(project_id, abbrevation, draughtproofing_stage_name, generic_tool_item_id)
    
    paginator = Paginator(filtered_projects, per_page=10, orphans=3)
    page = request.GET.get('page') # get the page number from the URL
    page_object = paginator.get_page(page)
    return render(request, 'filtered_projects_by_pm.html', context= {"projects" : page_object, 'airtightness_options' : airtightness_options, 'attic_options' : attic_options,
        'cwi_options' : cwi_options, 'draught_proofing_options' : draught_proofing_options, 'ewi_options' : ewi_options,
        'iwi_options' : iwi_options, 'mev_options' : mev_options, 'oil_boiler_options' : oil_boiler_options, 'pm_options' : pm_options,
        'oil_tank_options' : oil_tank_options, 'plumbing_options' : plumbing_options, 'rtv_options' : rtv_options, 'qc_options' : qc_options,
        'window_options' : window_options, 'stages_options' : stages_options, 'gni_options' : gni_options, 'esb_options' : esb_options, 
        'total_project_in_db' : filtered_projects_count, 'filter_stage' : filter_stage, 'page_object' : page_object})

@login_required(login_url='/accounts/login/')
def filter_projects_by_qc(request):
    if 'filter-by-qc' in request.POST:
        filter_stage = request.POST['filter-by-qc'] 
        request.session['filter-by-qc'] = filter_stage
    elif request.session.get('filter-by-qc'):
        filter_stage = request.session.get('filter-by-qc')
    else:
        redirect(dashboard)
    # print(filter_stage)
    filtered_projects = ProjectDetails.objects.filter(QC_STATUS=str(filter_stage)).values().order_by('project_name')
    filtered_projects_count = filtered_projects.count()
    airtightness_options = AirtightnessStatusID.objects.all()
    attic_options = AtticStatusID.objects.all()
    cwi_options = CwiStatusID.objects.all()
    draught_proofing_options = DraughtProofingStatusID.objects.all()
    ewi_options = EwiStatusID.objects.all()
    iwi_options = IwiStatusID.objects.all()
    mev_options = MevStatusID.objects.all()
    oil_boiler_options = OilBoilerStatusID.objects.all()
    oil_tank_options = OilTankStatusID.objects.all()
    plumbing_options = PlumbingStatusID.objects.all()
    rtv_options = RtvStatusID.objects.all()
    window_options = WindowStatusID.objects.all()
    stages_options = CompanyProjectStages.objects.all().order_by('project_stage_name')
    gni_options = GniStages.objects.all()
    esb_options = EsbStages.objects.all()
    qc_options = QcStages.objects.all()
    pm_options = ProjectManagers.objects.all()
    if request.method == 'POST':
        if 'stage' in request.POST:
            split_str_list = request.POST['stage'].split("_")
            main_stage_name = split_str_list[0]
            project_id = split_str_list[1]  
            response_status_code = update_procore_project_stage(project_id, main_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.project_stage = main_stage_name
                project_object.save()
        if 'gni' in request.POST:
            split_str_list = request.POST['gni'].split("_")
            gni_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            esb_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.GNI_STATUS = gni_stage_name
                project_object.save()
        if 'esb' in request.POST:
            split_str_list = request.POST['esb'].split("_")
            esb_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.ESB_STATUS = esb_stage_name
                project_object.save()
        if 'qc_mid_final' in request.POST:
            split_str_list = request.POST['qc_mid_final'].split("_")
            qc_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            esb_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.QC_STATUS = qc_stage_name
                project_object.save()
        if 'window' in request.POST:
            split_str_list = request.POST['window'].split("_")
            window_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.window_correspondence_id != 0:
                generic_tool_item_id = project_object.window_correspondence_id
                project_object.WINDOW_STATUS = window_stage_name
                project_object.save()
                abbrevation = 'WIN PO'
                update_procore_correspondence(project_id, abbrevation, window_stage_name, generic_tool_item_id)
        if 'cwi' in request.POST:
            split_str_list = request.POST['cwi'].split("_")
            cwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.cwi_correpondence_id != 0:
                generic_tool_item_id = project_object.cwi_correpondence_id
                project_object.CWI_STATUS = cwi_stage_name
                project_object.save()
                abbrevation = 'CWI PO'
                update_procore_correspondence(project_id, abbrevation, cwi_stage_name, generic_tool_item_id)
        if 'oil_boiler' in request.POST:
            split_str_list = request.POST['oil_boiler'].split("_")
            oil_boiler_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_boiler_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_boiler_correspondence_id
                project_object.OIL_BOILER_STATUS = oil_boiler_stage_name
                project_object.save()
                abbrevation = 'OBM PO'
                update_procore_correspondence(project_id, abbrevation, oil_boiler_stage_name, generic_tool_item_id)
        if 'oil_tank' in request.POST:
            split_str_list = request.POST['oil_tank'].split("_")
            oil_tank_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_tank_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_tank_correspondence_id
                project_object.OIL_TANK_STATUS = oil_tank_stage_name
                project_object.save()
                abbrevation = 'OTM PO'
                update_procore_correspondence(project_id, abbrevation, oil_tank_stage_name, generic_tool_item_id)
        if 'ewi' in request.POST:
            split_str_list = request.POST['ewi'].split("_")
            ewi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.ewi_correspondence_id != 0:
                generic_tool_item_id = project_object.ewi_correspondence_id
                project_object.EWI_STATUS = ewi_stage_name
                project_object.save()
                abbrevation = 'EWI PO'
                update_procore_correspondence(project_id, abbrevation, ewi_stage_name, generic_tool_item_id)
        if 'plumbing' in request.POST:
            split_str_list = request.POST['plumbing'].split("_")
            plumbing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.plumbing_correpondence_id != 0:
                generic_tool_item_id = project_object.plumbing_correpondence_id
                project_object.PLUMBING_STATUS = plumbing_stage_name
                project_object.save()
                abbrevation = 'PLUMB PO'
                update_procore_correspondence(project_id, abbrevation, plumbing_stage_name, generic_tool_item_id)
        if 'iwi' in request.POST:
            split_str_list = request.POST['iwi'].split("_")
            iwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.iwi_correspondence_id != 0:
                generic_tool_item_id = project_object.iwi_correspondence_id
                project_object.IWI_STATUS = iwi_stage_name
                project_object.save()
                abbrevation = 'IWI PO'
                update_procore_correspondence(project_id, abbrevation, iwi_stage_name, generic_tool_item_id)
        if 'airtightness' in request.POST:
            split_str_list = request.POST['airtightness'].split("_")
            airtightness_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.airtightness_correspondence_id != 0:
                generic_tool_item_id = project_object.airtightness_correspondence_id
                project_object.AIRTIGHTNESS_STATUS = airtightness_stage_name
                project_object.save()
                abbrevation = 'ATT PO'
                update_procore_correspondence(project_id, abbrevation, airtightness_stage_name, generic_tool_item_id)
        if 'rtv' in request.POST:
            split_str_list = request.POST['rtv'].split("_")
            rtv_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.rtv_correspondence_id != 0:
                generic_tool_item_id = project_object.rtv_correspondence_id
                project_object.RTV_STATUS = rtv_stage_name
                project_object.save()
                abbrevation = 'RV PO'
                update_procore_correspondence(project_id, abbrevation, rtv_stage_name, generic_tool_item_id)
        if 'mev' in request.POST:
            split_str_list = request.POST['mev'].split("_")
            mev_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.mev_correspondence_id != 0:
                generic_tool_item_id = project_object.mev_correspondence_id
                project_object.MEV_STATUS = mev_stage_name
                project_object.save()
                abbrevation = 'MEV PO'
                update_procore_correspondence(project_id, abbrevation, mev_stage_name, generic_tool_item_id)
        if 'attic' in request.POST:
            split_str_list = request.POST['attic'].split("_")
            attic_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.attic_correspondence_id != 0:
                generic_tool_item_id = project_object.attic_correspondence_id
                project_object.ATTIC_STATUS = attic_stage_name
                project_object.save()
                abbrevation = 'ATTIC PO'
                update_procore_correspondence(project_id, abbrevation, attic_stage_name, generic_tool_item_id)
        if 'draughtproofing' in request.POST:
            split_str_list = request.POST['draughtproofing'].split("_")
            draughtproofing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.draughtproofing_correspondence_id != 0:
                generic_tool_item_id = project_object.draughtproofing_correspondence_id
                project_object.DRAUGHTPROOFING_STATUS = draughtproofing_stage_name
                project_object.save()
                abbrevation = 'DP PO'
                update_procore_correspondence(project_id, abbrevation, draughtproofing_stage_name, generic_tool_item_id)
    
    paginator = Paginator(filtered_projects, per_page=10, orphans=3)
    page = request.GET.get('page') # get the page number from the URL
    page_object = paginator.get_page(page)
    return render(request, 'filtered_projects_by_qc.html', context= {"projects" : page_object, 'airtightness_options' : airtightness_options, 'attic_options' : attic_options,
        'cwi_options' : cwi_options, 'draught_proofing_options' : draught_proofing_options, 'ewi_options' : ewi_options,
        'iwi_options' : iwi_options, 'mev_options' : mev_options, 'oil_boiler_options' : oil_boiler_options, 'pm_options' : pm_options,
        'oil_tank_options' : oil_tank_options, 'plumbing_options' : plumbing_options, 'rtv_options' : rtv_options, 'qc_options' : qc_options,
        'window_options' : window_options, 'stages_options' : stages_options, 'gni_options' : gni_options, 'esb_options' : esb_options, 
        'total_project_in_db' : filtered_projects_count, 'filter_stage' : filter_stage, 'page_object' : page_object})

   
@login_required(login_url='/accounts/login/')
def search_projects(request):
    if 'search-input' in request.POST:
        search_input = request.POST['search-input'] 
        request.session['search-input'] = search_input
    elif request.session.get('search-input'):
        search_input = request.session.get('search-input')
    else:
        redirect(dashboard)
    # print(search_input)
    searched_projects = ProjectDetails.objects.filter(project_name__icontains=str(search_input)).values().order_by('project_name')
    search_projects_count = searched_projects.count()
    airtightness_options = AirtightnessStatusID.objects.all()
    attic_options = AtticStatusID.objects.all()
    cwi_options = CwiStatusID.objects.all()
    draught_proofing_options = DraughtProofingStatusID.objects.all()
    ewi_options = EwiStatusID.objects.all()
    iwi_options = IwiStatusID.objects.all()
    mev_options = MevStatusID.objects.all()
    oil_boiler_options = OilBoilerStatusID.objects.all()
    oil_tank_options = OilTankStatusID.objects.all()
    plumbing_options = PlumbingStatusID.objects.all()
    rtv_options = RtvStatusID.objects.all()
    window_options = WindowStatusID.objects.all()
    stages_options = CompanyProjectStages.objects.all().order_by('project_stage_name')
    gni_options = GniStages.objects.all()
    esb_options = EsbStages.objects.all()
    qc_options = QcStages.objects.all()
    pm_options = ProjectManagers.objects.all()
    if request.method == 'POST':
        if 'stage' in request.POST:
            split_str_list = request.POST['stage'].split("_")
            main_stage_name = split_str_list[0]
            project_id = split_str_list[1]  
            response_status_code = update_procore_project_stage(project_id, main_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.project_stage = main_stage_name
                project_object.save()
        if 'gni' in request.POST:
            split_str_list = request.POST['gni'].split("_")
            gni_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            esb_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.GNI_STATUS = gni_stage_name
                project_object.save()
        if 'esb' in request.POST:
            split_str_list = request.POST['esb'].split("_")
            esb_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            qc_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.ESB_STATUS = esb_stage_name
                project_object.save()
        if 'qc_mid_final' in request.POST:
            split_str_list = request.POST['qc_mid_final'].split("_")
            qc_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            gni_stage_name = ''
            esb_stage_name = ''
            response_status_code = update_procore_project(project_id, gni_stage_name, esb_stage_name, qc_stage_name)
            if response_status_code == 200:
                project_object = ProjectDetails.objects.get(project_id=project_id)
                project_object.QC_STATUS = qc_stage_name
                project_object.save()
        if 'window' in request.POST:
            split_str_list = request.POST['window'].split("_")
            window_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.window_correspondence_id != 0:
                generic_tool_item_id = project_object.window_correspondence_id
                project_object.WINDOW_STATUS = window_stage_name
                project_object.save()
                abbrevation = 'WIN PO'
                update_procore_correspondence(project_id, abbrevation, window_stage_name, generic_tool_item_id)
        if 'cwi' in request.POST:
            split_str_list = request.POST['cwi'].split("_")
            cwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.cwi_correpondence_id != 0:
                generic_tool_item_id = project_object.cwi_correpondence_id
                project_object.CWI_STATUS = cwi_stage_name
                project_object.save()
                abbrevation = 'CWI PO'
                update_procore_correspondence(project_id, abbrevation, cwi_stage_name, generic_tool_item_id)
        if 'oil_boiler' in request.POST:
            split_str_list = request.POST['oil_boiler'].split("_")
            oil_boiler_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_boiler_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_boiler_correspondence_id
                project_object.OIL_BOILER_STATUS = oil_boiler_stage_name
                project_object.save()
                abbrevation = 'OBM PO'
                update_procore_correspondence(project_id, abbrevation, oil_boiler_stage_name, generic_tool_item_id)
        if 'oil_tank' in request.POST:
            split_str_list = request.POST['oil_tank'].split("_")
            oil_tank_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.oil_tank_correspondence_id != 0:
                generic_tool_item_id = project_object.oil_tank_correspondence_id
                project_object.OIL_TANK_STATUS = oil_tank_stage_name
                project_object.save()
                abbrevation = 'OTM PO'
                update_procore_correspondence(project_id, abbrevation, oil_tank_stage_name, generic_tool_item_id)
        if 'ewi' in request.POST:
            split_str_list = request.POST['ewi'].split("_")
            ewi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.ewi_correspondence_id != 0:
                generic_tool_item_id = project_object.ewi_correspondence_id
                project_object.EWI_STATUS = ewi_stage_name
                project_object.save()
                abbrevation = 'EWI PO'
                update_procore_correspondence(project_id, abbrevation, ewi_stage_name, generic_tool_item_id)
        if 'plumbing' in request.POST:
            split_str_list = request.POST['plumbing'].split("_")
            plumbing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.plumbing_correpondence_id != 0:
                generic_tool_item_id = project_object.plumbing_correpondence_id
                project_object.PLUMBING_STATUS = plumbing_stage_name
                project_object.save()
                abbrevation = 'PLUMB PO'
                update_procore_correspondence(project_id, abbrevation, plumbing_stage_name, generic_tool_item_id)
        if 'iwi' in request.POST:
            split_str_list = request.POST['iwi'].split("_")
            iwi_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.iwi_correspondence_id != 0:
                generic_tool_item_id = project_object.iwi_correspondence_id
                project_object.IWI_STATUS = iwi_stage_name
                project_object.save()
                abbrevation = 'IWI PO'
                update_procore_correspondence(project_id, abbrevation, iwi_stage_name, generic_tool_item_id)
        if 'airtightness' in request.POST:
            split_str_list = request.POST['airtightness'].split("_")
            airtightness_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.airtightness_correspondence_id != 0:
                generic_tool_item_id = project_object.airtightness_correspondence_id
                project_object.AIRTIGHTNESS_STATUS = airtightness_stage_name
                project_object.save()
                abbrevation = 'ATT PO'
                update_procore_correspondence(project_id, abbrevation, airtightness_stage_name, generic_tool_item_id)
        if 'rtv' in request.POST:
            split_str_list = request.POST['rtv'].split("_")
            rtv_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.rtv_correspondence_id != 0:
                generic_tool_item_id = project_object.rtv_correspondence_id
                project_object.RTV_STATUS = rtv_stage_name
                project_object.save()
                abbrevation = 'RV PO'
                update_procore_correspondence(project_id, abbrevation, rtv_stage_name, generic_tool_item_id)
        if 'mev' in request.POST:
            split_str_list = request.POST['mev'].split("_")
            mev_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.mev_correspondence_id != 0:
                generic_tool_item_id = project_object.mev_correspondence_id
                project_object.MEV_STATUS = mev_stage_name
                project_object.save()
                abbrevation = 'MEV PO'
                update_procore_correspondence(project_id, abbrevation, mev_stage_name, generic_tool_item_id)
        if 'attic' in request.POST:
            split_str_list = request.POST['attic'].split("_")
            attic_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.attic_correspondence_id != 0:
                generic_tool_item_id = project_object.attic_correspondence_id
                project_object.ATTIC_STATUS = attic_stage_name
                project_object.save()
                abbrevation = 'ATTIC PO'
                update_procore_correspondence(project_id, abbrevation, attic_stage_name, generic_tool_item_id)
        if 'draughtproofing' in request.POST:
            split_str_list = request.POST['draughtproofing'].split("_")
            draughtproofing_stage_name = split_str_list[0]
            project_id = split_str_list[1]
            project_object = ProjectDetails.objects.get(project_id=project_id)
            if project_object.draughtproofing_correspondence_id != 0:
                generic_tool_item_id = project_object.draughtproofing_correspondence_id
                project_object.DRAUGHTPROOFING_STATUS = draughtproofing_stage_name
                project_object.save()
                abbrevation = 'DP PO'
                update_procore_correspondence(project_id, abbrevation, draughtproofing_stage_name, generic_tool_item_id)
    paginator = Paginator(searched_projects, per_page=10, orphans=3)
    page = request.GET.get('page') # get the page number from the URL
    page_object = paginator.get_page(page)
    return render(request, 'searched_projects.html', context= {"projects" : page_object, 'airtightness_options' : airtightness_options, 'attic_options' : attic_options,
        'cwi_options' : cwi_options, 'draught_proofing_options' : draught_proofing_options, 'ewi_options' : ewi_options,
        'iwi_options' : iwi_options, 'mev_options' : mev_options, 'oil_boiler_options' : oil_boiler_options,'pm_options' : pm_options,
        'oil_tank_options' : oil_tank_options, 'plumbing_options' : plumbing_options, 'rtv_options' : rtv_options, 'qc_options' : qc_options,
        'window_options' : window_options, 'stages_options' : stages_options, 'gni_options' : gni_options, 'esb_options' : esb_options, 
        'total_project_in_db' : search_projects_count, 'search_input' : search_input, 'page_object' : page_object})


@login_required(login_url='/accounts/login/')
def export_to_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="projects_excel.xlsx"'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'WHS Projects'

    # Write header row
    header = ['Project ID', 'Main Project Stage', 'Project Name', 'GNI', 'ESB', 'WINDOW', 'CWI', 'OIL_BOILER', 'OIL_TANK', 'EWI', 'PLUMBING', 'IWI', 'QC STATUS', 'AIRTIGHTNESS', 'RTV', 'MEV', 'ATTIC', 'DRAUGHTPROOFING']
    for col_num, column_title in enumerate(header, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = column_title

    # Write data rows
    queryset = ProjectDetails.objects.all().values_list('project_number', 'project_stage', 'project_name', 'GNI_STATUS', 'ESB_STATUS', 'WINDOW_STATUS', 'CWI_STATUS', 'OIL_BOILER_STATUS', 'OIL_TANK_STATUS', 'EWI_STATUS', 'PLUMBING_STATUS', 'IWI_STATUS', 'QC_STATUS', 'AIRTIGHTNESS_STATUS', 'RTV_STATUS', 'MEV_STATUS', 'ATTIC_STATUS', 'DRAUGHTPROOFING_STATUS')
    for row_num, row in enumerate(queryset, 1):
        for col_num, cell_value in enumerate(row, 1):
            cell = worksheet.cell(row=row_num+1, column=col_num)
            cell.value = cell_value

    workbook.save(response)

    return response

########################################################################################################
# Procore API functions for updating Procore and updating database
########################################################################################################

def update_procore_project_stage(project_id, project_stage):
    access_token = get_acess_token()
    company_id = get_company_id()
    project_stage_object = CompanyProjectStages.objects.get(project_stage_name=project_stage)
    project_stage_id = project_stage_object.project_stage_id
    print(project_id, project_stage_id)
    url = BASE_URL + '/rest/v1.0/projects/'+str(project_id)
    headers = {
        "Authorization": "Bearer " + access_token,
        'Procore-Company-Id': str(company_id),
        'content-type': "application/json",
    }
    payload = {
        'company_id' : str(company_id),
        'project' : {
            'project_stage_id' : project_stage_id, 
        }
    }
    # print(payload)
    response = requests.patch(url, headers=headers, json=payload)
    response_status_code = response.status_code
    print(response_status_code)
    return response_status_code

def update_procore_project(project_id, GNI_STATUS, ESB_STATUS, QC_STATUS):
    access_token = get_acess_token()
    company_id = get_company_id()
    GNI_custom_filed_id = 'custom_field_64774'
    ESB_custom_field_id = 'custom_field_64772'
    QC_custom_field_id = 'custom_field_67252'
    # print(project_id, GNI_STATUS, ESB_STATUS)
    url = BASE_URL + '/rest/v1.0/projects/'+str(project_id)
    headers = {
        "Authorization": "Bearer " + access_token,
        'Procore-Company-Id': str(company_id),
        'content-type': "application/json",
    }
    if GNI_STATUS != '':
        gni_stage_object = GniStages.objects.get(gni_stage_name=GNI_STATUS)
        gni_stage_id = gni_stage_object.gni_stage_id
        # print(gni_stage_id)
        payload = {
            'company_id' : str(company_id),
            'run_configurable_validations' : True,
            'project' : {
                GNI_custom_filed_id : gni_stage_id
            }
        }
    elif ESB_STATUS != '':
        esb_stage_object = EsbStages.objects.get(esb_stage_name=ESB_STATUS)
        esb_stage_id = esb_stage_object.esb_stage_id
        # print(esb_stage_id)
        payload = {
            'company_id' : str(company_id),
            'run_configurable_validations' : True,
            'project' : {
                ESB_custom_field_id : esb_stage_id
            }
        }
    elif QC_STATUS != '':
        qc_stage_object = QcStages.objects.get(qc_stage_name=QC_STATUS)
        qc_stage_id = qc_stage_object.qc_stage_id
        # print(esb_stage_id)
        payload = {
            'company_id' : str(company_id),
            'run_configurable_validations' : True,
            'project' : {
                QC_custom_field_id : qc_stage_id
            }
        }
    print(payload)
    response = requests.patch(url, headers=headers, json=payload)
    response_status_code = response.status_code
    print(response_status_code)
    # response_json = response.json()
    return response_status_code


def update_procore_correspondence(project_id, abbreviation, status, generic_tool_item_id):
    access_token = get_acess_token()
    company_id = get_company_id()
    generic_tool_id = DICT_OF_CORRESPONDENCES[abbreviation]
    print(generic_tool_item_id)
    url = BASE_URL + '/rest/v1.0/projects/'+str(project_id)+'/generic_tools/'+str(generic_tool_id)+'/generic_tool_items/'+str(generic_tool_item_id)
    headers = {
        "Authorization": "Bearer " + access_token,
        'Procore-Company-Id': str(company_id)
    }
    payload = {
        'status' : status, 
    }
    response = requests.patch(url, headers=headers, json=payload)
    response_status_code = response.status_code
    print(response_status_code)
    # response_json = response.json()
    # print(response_json)
    return response_status_code

#######################################################################################################
# Scheduling functions to keep DB uptodate
#######################################################################################################

scheduler = BackgroundScheduler(daemon=True, job_defaults={'max_instances': 10})
scheduler.add_job(lambda: get_all_correspondences_for_the_project(), 'interval', minutes=60)

scheduler.add_job(lambda: clean_db_for_fresh_projects(), 'cron', hour=23)
scheduler.add_job(lambda: clean_db_for_fresh_statuses(), 'cron', hour=23)
scheduler.add_job(lambda: get_all_active_whs_projects(), 'cron', hour=23)
scheduler.add_job(lambda: get_lov_entries_statuses(), 'cron', hour=23)
scheduler.add_job(lambda: save_company_stages(), 'cron', hour=23)
scheduler.add_job(lambda: get_all_generic_tools(), 'cron', hour=23)
scheduler.add_job(lambda: get_generic_tool_statuses(), 'cron', hour=23)

# scheduler.add_job(lambda : scheduler.print_jobs(),'interval',seconds=5)
scheduler.start()

#######################################################################################################
# The End 
#######################################################################################################
