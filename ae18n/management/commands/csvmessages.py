from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from ae18n.po2csv import get_csv_for_lang


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-l', '--locale', dest='locale'),
    )

    def handle(self, *args, **opts):
        if not opts.get('locale'):
            raise CommandError('Need a locale')

        return get_csv_for_lang(opts['locale']).getvalue()
