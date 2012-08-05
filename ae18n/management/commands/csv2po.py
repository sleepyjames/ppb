import os
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ae18n.po2csv import get_po_for_lang, csv2po


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-l', '--locale', dest='locale'),
        make_option('-f', '--file', dest='file',
            help="Path to .csv file to conver to .po"),
    )

    def handle(self, *args, **opts):
        if not opts.get('locale') in dict(settings.LANGUAGES):
            raise CommandError('Need a locale')

        filepath = opts.get('file')
        if not filepath or not os.path.exists(filepath):
            raise CommandError('csv file at %s does not exist' % filepath)

        lang = opts['locale']
        master_po = get_po_for_lang(lang)
        csv = open(filepath)
        pot = csv2po(csv)
        csv.close()
        #master_po.merge(pot)
        return unicode(pot)
