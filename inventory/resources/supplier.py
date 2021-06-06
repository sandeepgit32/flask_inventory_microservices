from flask_restful import Resource
from flask import request
from models.supplier import SupplierModel
from schemas.supplier import SupplierSchema
from libs.strings import gettext

supplier_schema = SupplierSchema()
supplier_list_schema = SupplierSchema(many=True)


class Supplier(Resource):
    # GET /supplier/<string:id>
    @classmethod
    def get(cls, id: int):
        supplier = SupplierModel.find_by_id(id)
        if supplier:
            return supplier_schema.dump(supplier), 200

        return {"message": gettext("supplier_not_found")}, 404


    # DELETE /supplier/<string:id>
    @classmethod
    def delete(cls, id: int):
        supplier = SupplierModel.find_by_id(id)
        if supplier:
            supplier.delete_from_db()
            return {"message": gettext("supplier_deleted")}, 200

        return {"message": gettext("supplier_not_found")}, 404


    # PUT /supplier/<string:id>
    @classmethod
    def put(cls, id: int):
        # When a client needs to replace an existing Resource entirely, they can use PUT. 
        # When they're doing a partial update, they can use HTTP PATCH.
        supplier_json = request.get_json()
        supplier = SupplierModel.find_by_id(id)

        if supplier:
            # Dynamically setting attributes of the object 'supplier' from 'supplier_json' dict
            for attribute in supplier_json.keys():
                setattr(supplier, attribute, supplier_json[attribute])
            supplier.save_to_db()
        else:
            return {"message": gettext("supplier_not_found")}, 404

        return supplier_schema.dump(supplier), 200


class SupplierList(Resource):
    # GET /suppliers
    @classmethod
    def get(cls):
        return {"suppliers": supplier_list_schema.dump(SupplierModel.find_all())}, 200

    # POST /suppliers
    @classmethod
    def post(cls):
        supplier_json = request.get_json()
        print('request', request.headers)
        supplier_name = supplier_json["name"]

        if SupplierModel.find_by_name(supplier_name):
            return {"message": gettext("supplier_exists").format(supplier_name)}, 400

        supplier = supplier_schema.load(supplier_json)

        try:
            supplier.save_to_db()
        except:
            return {"message": gettext("supplier_error_inserting")}, 500

        return supplier_schema.dump(supplier), 201
