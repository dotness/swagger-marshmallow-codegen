# -*- coding:utf-8 -*-
import logging
import sys
import json
from collections import OrderedDict
import dictknife
from .langhelpers import titleize, normalize
from .dispatcher import Pair
from . import validate
logger = logging.getLogger(__name__)


class Accessor(object):
    def __init__(self):
        self.resolver = Resolver()

    def definitions(self, d):
        return d.get("definitions") or {}

    def properties(self, d):
        return d.get("properties") or {}

    def type_and_format(self, name, field, ignore_array=True):
        try:
            if self.resolver.has_many(field):
                return self.type_and_format(name, field["items"])
            typ = field["type"]
            format = field.get("format")
            logger.debug("type-and-format: name=%s type=%s, format=%s, field=%s", name, typ, format, lazy_json_dump(field))
            return Pair(type=typ, format=format)
        except KeyError as e:
            logger.debug("%s is not found. name=%s", e.args[0], name)
            if "enum" in field:
                return Pair(type="string", format=None)
            if not field:
                return Pair(type="any", format=None)
            return Pair(type="object", format=None)

    def update_options_pre_properties(self, d, opts):
        for name in d.get("required") or []:
            opts[name]["required"] = True
        return opts

    def update_option_on_property(self, c, field, opts):
        if "description" in field:
            opts["description"] = field["description"]
        if self.resolver.has_many(field):
            opts["many"] = True
        if "default" in field:
            # todo: import on datetime.datetime etc...
            opts["default"] = field["default"]  # xxx
        return self.update_validate_option_on_property(c, field, opts)

    def update_validate_option_on_property(self, c, field, opts):
        validators = []
        # range
        if "minimum" in field or "maximum" in field:
            range_opts = OrderedDict(c=c)
            range_opts["min"] = field.get("minimum")
            range_opts["exclusive_min"] = field.get("exclusiveMinimum", False)
            range_opts["max"] = field.get("maximum")
            range_opts["exclusive_max"] = field.get("exclusiveMaximum", False)
            validators.append(validate.RangeWithRepr(**range_opts))
        if validators:
            opts["validate"] = validators
        return opts


class Resolver(object):
    def __init__(self):
        self.accessor = dictknife.Accessor()  # todo: rename

    def has_ref(self, d):
        return "$ref" in d

    def has_schema(self, fulldata, d, cand=("object",), fullscan=True):
        typ = d.get("type", None)
        if typ in cand:
            return True
        if "properties" in d:
            return True
        if not self.has_ref(d):
            return False
        if not fullscan:
            return False
        _, definition = self.resolve_ref_definition(fulldata, d)
        return self.has_schema(fulldata, definition, fullscan=False)

    def has_nested(self, fulldata, d):
        if self.has_schema(fulldata, d, fullscan=False):
            return True
        return self.has_many(d) and self.has_schema(fulldata, d["items"])

    def has_many(self, d):
        return d.get("type") == "array" or "items" in d

    def resolve_normalized_name(self, name):
        return normalize(name)

    def resolve_schema_name(self, name):
        schema_name = titleize(name)
        logger.debug("schema: %s", schema_name)
        return schema_name

    def resolve_ref_definition(self, fulldata, d, name=None, i=0, level=-1):
        # return schema_name, definition_dict
        # todo: support quoted "/"
        # on array
        if "items" in d:
            definition = d
            name, _ = self.resolve_ref_definition(fulldata, d["items"], name=name, i=i, level=level + 1)  # xxx
            return name, definition

        if "$ref" not in d:
            return self.resolve_schema_name(name), d
        if level == 0:
            return self.resolve_schema_name(name), d

        logger.debug("%sref: %r", "  " * i, d["$ref"])

        path = d["$ref"][len("#/"):].split("/")
        name = path[-1]

        parent = self.accessor.maybe_access_container(fulldata, path)
        if parent is None:
            sys.stderr.write("\t{!r} is not found\n".format(d["$ref"]))
            return self.resolve_schema_name(name), d
        return self.resolve_ref_definition(fulldata, parent[name], name=name, i=i + 1, level=level - 1)


class LazyCallString(object):
    def __init__(self, call, *args, **kwargs):
        self.call = call
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.call(*self.args, **self.kwargs)


def lazy_json_dump(s):
    return LazyCallString(json.dumps, s)