from app import ma
from models.transaction import TransactionModel


class TransactionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionModel
        load_instance = True 
        # load_only = ("store",)
        # dump_only = ("id",)
