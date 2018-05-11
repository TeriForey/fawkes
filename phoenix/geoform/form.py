import os
from UserDict import DictMixin

import colander
from pyramid.security import authenticated_userid
from pyramid.compat import urlparse


class BBoxValidator(object):
    """
    Bounding-Box validator which succeeds if the bbox value has the format
    :attr:`minx,miny,maxx,maxy` and values are in range (``-180 <= x <=180``, ``-90 <= y <=90``).
    """
    def __call__(self, node, value):
        try:
            minx, miny, maxx, maxy = [float(val) for val in value.split(',', 3)]
        except Exception:
            raise colander.Invalid(node, "Could not parse BBox.")
        else:
            if minx < -180 or minx > 180:
                raise colander.Invalid(node, "MinX out of range [-180, 180].")
            if miny < -90 or miny > 90:
                raise colander.Invalid(node, "MinY out of range [-90, 90].")
            if maxx < -180 or maxx > 180:
                raise colander.Invalid(node, "MaxX out of range [-180, 180].")
            if maxy < -90 or maxy > 90:
                raise colander.Invalid(node, "MaxY out of range [-90, 90].")
            if minx > maxx:
                raise colander.Invalid(node, "MinX greater than MaxX")
            if miny > maxy:
                raise colander.Invalid(node, "MinY greater than MaxY")


class RangeValidator(object):
    """
    Range validator which succeeds if the seperator is a dash, both numbers can be converted to ints and
    the min < max and min > 0
    """
    def __call__(self, node, value):
        try:
            min, max = [int(val.strip()) for val in value.split('-',1)]
        except Exception:
            raise colander.Invalid(node, "Could not parse range. "
                                         "Is the minimum less than 0? Are the values separated by a '-'?")
        else:
            if min < 0:
                raise colander.Invalid(node, "Range minimum is less than 0")
            if max < min:
                raise colander.Invalid(node, "Min is greater than Max")
            if max > 15000:
                raise colander.Invalid(node, "Max is greater than allowed dispersion domains (15000m)")


class LongitudeValidator(object):
    """
    Longitude validator to ensure any input values are between [-180,180]
    """
    def __call__(self, node, value):
        try:
            lon = float(value)
        except Exception:
            raise colander.Invalid(node, "Value entered is not a number")
        else:
            if lon < -180 or lon > 180:
                raise colander.Invalid(node, "Longitude out of range [-180, 180].")


class LatitudeValidator(object):
    """
    Latitude validator to ensure any input values are between [-90,90]
    """
    def __call__(self, node, value):
        try:
            lat = float(value)
        except Exception:
            raise colander.Invalid(node, "Value entered is not a number")
        else:
            if lat < -90 or lat > 90:
                raise colander.Invalid(node, "Latitude out of range [-90, 90].")
            
            
class LongitudeBoundaryValidator(object):
    """
    Longitude boundary validator to ensure input string is a tuple between [-180,180]
    """
    def __call__(self, node, value):
        try:
            minval, maxval = [float(val.strip()) for val in value.split(',', 1)]
        except Exception:
            raise colander.Invalid(node, "Longitude boundary should be separated with a comma (min,max)")
        else:
            if minval < -180 or maxval > 180:
                raise colander.Invalid(node, "Longitude is out of range [-180, 180]")
            if minval >= maxval:
                raise colander.Invalid(node, "Minimum longitude is greater than maximum")


class LatitudeBoundaryValidator(object):
    """
    Latitude boundary validator to ensure input string is a tuple between [-90,90]
    """
    def __call__(self, node, value):
        try:
            minval, maxval = [float(val.strip()) for val in value.split(',', 1)]
        except Exception:
            raise colander.Invalid(node, "Latitude boundary should be separated with a comma (min,max)")
        else:
            if minval < -90 or maxval > 90:
                raise colander.Invalid(node, "Latitude is out of range [-90, 90]")
            if minval >= maxval:
                raise colander.Invalid(node, "Minimum latitude is greater than maximum")
            

class TupleFloatValidator(object):
    """
    Float tuple validator
    """
    def __call__(self, node, value):
        try:
            val1, val2 = [float(val.strip()) for val in value.split(',', 1)]
        except Exception:
            raise colander.Invalid(node, "Could not read comma-separated numbers")


class LonLatTupleValidator(object):
    """
    Longitude, Latitude tuple validator
    """
    def __call__(self, node, value):
        try:
            lon, lat = [float(val.strip()) for val in value.split(',', 1)]
        except Exception:
            raise colander.Invalid(node, "Could not read comma-separated coordinates (Longitude,Latitude)")
        else:
            if lon < -180 or lon > 180:
                raise colander.Invalid(node, "Longitude out of range [-180,180]")
            if lat < -90 or lat > 90:
                raise colander.Invalid(node, "Latitude out of range [-90,90]")


class URLValidator(object):
    """
    URL validator which can configured with allowed URL schemes.
    """
    def __init__(self, allowed_schemes=None):
        self.allowed_schemes = allowed_schemes or ['http', 'https']

    def __call__(self, node, value):
        try:
            parsed_url = urlparse.urlparse(value)
        except Exception:
            raise colander.Invalid(node, "Invalid URL.")
        else:
            if parsed_url.scheme not in self.allowed_schemes:
                raise colander.Invalid(node, "URL scheme {} is not allowed.".format(parsed_url.scheme))
            if not parsed_url.netloc:
                raise colander.Invalid(node, "Invalid URL.")
            if '..' in parsed_url.path:
                raise colander.Invalid(node, "Invalid URL.")


class TextValidator(object):
    """
    """
    def __init__(self, restricted_chars=None):
        self.restricted_chars = restricted_chars or ["\\", "#", ";", "&", "!", "<", ">"]

    def __call__(self, node, value):
        try:
            normalized_value = str(value).strip()
        except Exception:
            raise colander.Invalid(node, "Invalid value.")
        else:
            if not normalized_value:
                raise colander.Invalid(node, "Invalid value ... empty.")
            for char in self.restricted_chars:
                if char in normalized_value:
                    raise colander.Invalid(node, "Invalid value ... contains restricted characters.")


class FileUploadValidator(colander.All):
    """
    Runs all validators for file upload checks.
    """
    def __init__(self, storage, max_size):
        self.validators = [FileFormatAllowedValidator(storage), FileSizeLimitValidator(storage, max_size)]


class FileFormatAllowedValidator(object):
    """
    File format extension is allowed.

    https://pythonhosted.org/pyramid_storage/
    """
    def __init__(self, storage):
        self.storage = storage

    def __call__(self, node, value):
        if not self.storage.filename_allowed(value['filename']):
            msg = 'File format is not allowed: {filename}'.format(filename=value['filename'])
            raise colander.Invalid(node, msg)


class FileSizeLimitValidator(object):
    """
    File size limit validator.

    You can configure the maximum size by setting the max_size
    option to the maximum number of megabytes that you want to allow.
    """
    def __init__(self, storage, max_size=2):
        self.storage = storage
        self.max_size = max_size

    def __call__(self, node, value):
        value['fp'].seek(0, 2)
        size = value['fp'].tell()
        value['fp'].seek(0)
        if size > int(self.max_size) * 1024 * 1024:
            msg = 'Maximum file size: {size}MB'.format(size=self.max_size)
            raise colander.Invalid(node, msg)
