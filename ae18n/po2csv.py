import os, csv
from StringIO import StringIO

from django.conf import settings

from rosetta import polib

from utils import escape, unescape, bool2str, str2bool


"""

Functions for converting .po files into .csv files and back again.

"""


# How the different plural translation forms are separated
PLURAL_SEPARATOR = '\n\n'

PO_ATTRIBUTES = ['msgid', 'msgid_plural', 'msgctxt', 'msgstr_plural',
    'fuzzy', 'comments', 'obsolete']

# Headers for the csv representation of the .po file
CSV_HEADERS = {
    'msgid': 'Original string',
    'msgid_plural': 'Original string in plural form',
    'msgctxt': 'String context',
    'msgstr_plural': """Translations (translations for separate plural forms 
should be separated by a linebreak, alt+enter)""",
    'fuzzy': 'Is this a rough translation? (y/n, default n)',
    'comments': 'Comments for translators',
    'obsolete': 'Is this translation no longer used?'
}

csv_header_rows = [PO_ATTRIBUTES, [CSV_HEADERS[k] for k in PO_ATTRIBUTES]]


def get_po_from_filepath(path):
    """Get the .po file at the given path and raise an error if it
    doesn't exist.
    """
    if not os.path.exists(path):
        raise IOError('File not found at path %s' % path)
    return polib.pofile(path)


def get_po_for_lang(lang, domain='django'):
    """Get the .po file for the given language code and domain. Currently it
    assumes that the .po files are kept in the usual place:
    
        <proj_dir>/locale/<lang>/LC_MESSAGES/<domain>.po

    TODO: make this a setting or piggy back off of Django's knowledge of this.
    """
    # TODO: definitely change this temporary hack (couldn't be arsed to type
    #       the abs path to the project directory)
    #abs_path = os.path.normpath(os.path.dirname(__file__))
    po_name = '%s.po' % domain

    filepath = os.path.join(settings.PROJDIR, 'locale', lang, 'LC_MESSAGES', po_name)
    return get_po_from_filepath(filepath)


def get_csv_for_lang(lang, domain='django'):
    """Get the csv representation of the .po file for the given language.
    TODO: take `domain` as a kwarg.
    """
    return po2csv(get_po_for_lang(lang, domain=domain))


def force_plurals(entry):
    """A po file's plural handling is slightly weird. If there are no plurals
    for a translation:
        
        msgid "hello"
        msgstr "hola"

    If there are plurals however:

        msgid "%(count)s house"
        msgid_plural "%(count)s houses"
        msgstr[0] "%(count)s casa"
        msgstr[1] "%(count)s casas"

    So to keep things consistent, we force non-plural translations into the
    plural form for consistency, and then reading them back, we still have
    enough information to convert them back into singular translations if
    that's what they were meant to be.
    """
    plurals = entry.msgstr_plural
    if not plurals:
        plurals = {u'0': escape(entry.msgstr)}
    sorted_plurals = sorted(plurals.items(), key=lambda t: t[0])

    return PLURAL_SEPARATOR.join(escape(v) for k, v in sorted_plurals)


def undo_plurals(has_plural, plurals):
    """Undo what `force_plurals` does in order to figure out if just `msgstr`
    or `msgstr[x]` should be set. Returns `(singular_msgstr, plural_msgstr_map)`
    """
    plurals_list = plurals.split(PLURAL_SEPARATOR)
    plurals_dict = {}

    for i, p in enumerate(plurals_list):
        plurals_dict[unicode(i)] = unescape(p)

    if has_plural:
        return '', plurals_dict
    return plurals_dict.get('0', ''), {}


def po2csv(po):
    """Converts a polib.POFile object to a csv string (contained in an instance
    of StringIO)
    """
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)

    for header_row in csv_header_rows:
        csv_writer.writerow(header_row)

    for entry in po:

        msgstrs = force_plurals(entry)
        fuzzy = bool2str('fuzzy' in entry.flags, empty_for_false=True)
        obsolete = bool2str(entry.obsolete, empty_for_false=True)

        row = [
            escape(entry.msgid),
            escape(entry.msgid_plural),
            entry.msgctxt,
            msgstrs,
            fuzzy,
            entry.comment,
            obsolete
        ]
        csv_writer.writerow(row)

    return csv_file


def csv2po(csv_file):
    """Convert a file-like object `csv_file` to a polib.POFile object"""
    po = polib.POFile()

    # Reset to reading from the beginning of the file
    csv_file.seek(0)
    csv_reader = csv.reader(csv_file)

    for count, row in enumerate(csv_reader):
        # Skip the first two header rows
        if count < len(csv_header_rows):
            continue

        msgid = unescape(row[0])
        msgid_plural = unescape(row[1])
        msgctxt = row[2]
        msgstr, msgstr_plural = undo_plurals(msgid_plural, row[3])

        entry = polib.POEntry()
        entry.msgid = msgid

        if msgid_plural:
            entry.msgid_plural = msgid_plural
        if msgctxt:
            entry.msgctxt = msgctxt
        if msgstr:
            entry.msgstr = msgstr
        if msgstr_plural:
            entry.msgstr_plural = msgstr_plural

        po.append(entry)

    return po

