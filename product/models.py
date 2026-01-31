from db import db


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(100))
    price_buy = db.Column(db.Float)
    price_sell = db.Column(db.Float)
    measure_unit = db.Column(db.String(20))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    def to_dict(self, include_supplier=False, supplier_data=None):
        data = {
            'id': self.id,
            'product_code': self.product_code,
            'name': self.name,
            'category': self.category,
            'price_buy': self.price_buy,
            'price_sell': self.price_sell,
            'measure_unit': self.measure_unit,
            'supplier_id': self.supplier_id
        }
        
        if include_supplier and supplier_data:
            data['supplier'] = supplier_data
        
        return data
