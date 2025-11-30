from ma import ma
from models.warehouse import WarehouseModel


class WarehouseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WarehouseModel
        load_instance = True 
        # load_only = ("store",)
        # dump_only = ("id",)
