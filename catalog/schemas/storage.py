from ma import ma
from models.storage import StorageModel


class StorageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = StorageModel
        load_instance = True
        include_fk = True