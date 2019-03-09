from marshmallow import Schema, SchemaOpts, fields
from marshmallow import pre_load, pre_dump


class PrimitiveValueSchema:
    schema_class = None
    key = "value"
    missing_value = None

    def __init__(self, *args, **kwargs):
        self.schema = self.__class__.schema_class(*args, **kwargs)

    def load(self, value):  # don't support many
        data = {self.key: value}
        r = self.schema.load(data)
        return r.get(self.key) or self.missing_value

    def dump(self, value):  # don't support many
        data = {self.key: value}
        r = self.schema.dump(data)
        return r.get(self.key) or self.missing_value


class AdditionalPropertiesOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        super().__init__(meta, **kwargs)
        self.additional_field = getattr(meta, "additional_field", fields.Field)


class AdditionalPropertiesSchema(Schema):
    """
    support addtionalProperties

    class MySchema(AdditionalPropertiesSchema):
        class Meta:
            additional_field = fields.Integer()
    """

    OPTIONS_CLASS = AdditionalPropertiesOpts

    @pre_load
    @pre_dump
    def wrap_dynamic_additionals(self, data):
        diff = set(data.keys()).difference(self.fields.keys())
        for name in diff:
            f = self.opts.additional_field
            self.fields[name] = f() if callable(f) else f
        return data

    def dumps(self, obj, many=None, *args, **kwargs):
        return super().dumps(
            obj, many=many, *args, **kwargs
        )

    def dump(self, obj, many=None, *args, **kwargs):
        return super().dump(
            obj, many=many, *args, **kwargs
        )
