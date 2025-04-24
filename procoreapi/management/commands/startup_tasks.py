from django.core.management.base import BaseCommand, CommandError
from procoreapi.views import *

class Command(BaseCommand):
    help = 'My custom startup command'

    def handle(self, *args, **kwargs):
        try:
            # put startup code here
            get_all_active_whs_projects()
            get_lov_entries_statuses()
            save_company_stages()
            get_all_generic_tools()
            get_generic_tool_statuses()
            get_all_correspondences_for_the_project()
        except Exception as e:
            # raise CommandError('Initalization failed.')
            print(e.args)
