# -*- coding: utf-8 -*-


from django.utils.translation import ugettext_lazy as _

_messages_by_code = {}


def e(code, message, fatal):
    _messages_by_code[code] = message
    return (code, message, fatal)


def get_message(code):
    return _messages_by_code[code]


def is_itree_error_code(code):
    return 60 <= code <= 69

######################################
# FILE LEVEL ERRORS
######################################
#
# Errors that are attributed to the file and prevent the
# rows from being loaded and validated.
#
EMPTY_FILE = e(1, _('No rows found'), True)
UNMATCHED_FIELDS = e(3, _('Unrecognized fields in header row'), False)
MISSING_FIELD = e(5, _('This field is required'), True)
GENERIC_ERROR = e(
    6, _('An exception was raised while uploading the file'), True)

######################################
# ROW LEVEL ERRORS
######################################
#
# Errors that are attributed to rows
#
INVALID_GEOM = e(10, _('Longitude must be between -180 and 180 (inclusive) '
                       'and latitude must be between -90 and 90 (exclusive)'),
                 True)

GEOM_OUT_OF_BOUNDS = e(
    11, _('Geometry must be inside the map bounds'), True)

EXCL_ZONE = e(12, _('Geometry may not be in an exclusion zone'), True)

INVALID_SPECIES = e(20, _('Could not find this scientific name on the '
                          'master species list.'), True)
DUPLICATE_SPECIES = e(21, _('More than one species matches the given '
                            'scientific name.'), True)

INVALID_PLOT_ID = e(30, _('The given OpenTreeMap Planting Site ID does not '
                          'exist in the system. This ID is automatically '
                          'generated by OpenTreeMap and should only '
                          'be used for updating existing records'), True)
INVALID_TREE_ID = e(31, _('The given OpenTreeMap Tree ID does not exist '
                          'in the system. This ID is automatically '
                          'generated by OpenTreeMap and should only '
                          'be used for updating existing records'), True)
PLOT_TREE_MISMATCH = e(32, _('The planting site specified by the given '
                             'OpenTreeMap Planting Site ID does not contain '
                             'the tree specified by the given OpenTreeMap '
                             'Tree ID'), True)

FLOAT_ERROR = e(40, _('Not formatted as a number'), True)
POS_FLOAT_ERROR = e(41, _('Not formatted as a positive number'), True)
INT_ERROR = e(42, _('Not formatted as an integer'), True)
POS_INT_ERROR = e(43, _('Not formatted as a positive integer'), True)
BOOL_ERROR = e(44, _('Not formatted as a boolean'), True)
STRING_TOO_LONG = e(45, _('Strings must be less than 255 characters'),
                    True)
INVALID_DATE = e(46, _('Invalid date (must by YYYY-MM-DD)'), True)

INVALID_UDF_VALUE = e(50, _('Invalid value for custom field'), True)

INVALID_ITREE_REGION = e(60, _('Unknown i-Tree region'), True)
ITREE_REGION_NOT_IN_INSTANCE = e(
    61, _('i-Tree region not valid for this treemap'), True)
INVALID_ITREE_CODE = e(62, _('Unknown i-Tree code'), True)
ITREE_CODE_NOT_IN_REGION = e(
    63, _('i-Tree code not defined for region'), True)
INSTANCE_HAS_NO_ITREE_REGION = e(64, _('This treemap intersects no '
                                       'i-Tree regions and has no '
                                       'default region'), True)
INSTANCE_HAS_MULTIPLE_ITREE_REGIONS = e(
    65, _('This treemap intersects more than one i-Tree region'), True)

MERGE_REQUIRED = e(71, _('This row must be merged'), False)

NEARBY_TREES = e(
    1050, _('There are already trees within ten feet of this one'), False)
DUPLICATE_TREE = e(
    1051, _('There is already a tree at the specified location'), True)

SPECIES_DBH_TOO_HIGH = e(1060,
                         _('The diameter is too large for this species'),
                         False)

SPECIES_HEIGHT_TOO_HIGH = e(1061,
                            _('The height is too large for this species'),
                            False)
