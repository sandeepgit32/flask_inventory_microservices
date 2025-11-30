from ma import ma
from models.supplier import SupplierModel


class SupplierSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SupplierModel
        load_instance = True 
        # load_only = ("store",)
        # dump_only = ("id",)
