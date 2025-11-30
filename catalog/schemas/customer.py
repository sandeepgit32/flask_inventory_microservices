from ma import ma
from models.customer import CustomerModel


class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CustomerModel
        load_instance = True 
        # load_only = ("store",)
        # dump_only = ("id",)
        include_fk = True