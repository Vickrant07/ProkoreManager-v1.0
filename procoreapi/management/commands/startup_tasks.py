from django.core.management.base import BaseCommand, CommandError
from procoreapi.views import *

class Command(BaseCommand):
    help = 'My custom startup command'

    def handle(self, *args, **kwargs):
        try:
            # put startup code here
            get_all_active_OSS_and_NISEP_projects()
            get_lov_entries_statuses()
            save_company_stages()
        except Exception as e:
            # raise CommandError('Initalization failed.')
            print(e.args)

