from marshmallow import (
    Schema,
    fields
)
from swagger_marshmallow_codegen.validate import (
    ItemsRange,
    Unique
)


class A(Schema):
    nums = fields.List(fields.Integer(), validate=[ItemsRange(min=1, max=10, min_inclusive=True, max_inclusive=True), Unique()])
