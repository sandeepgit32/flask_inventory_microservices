from datetime import datetime
from db import db


class CustomerTransaction(db.Model):
    __tablename__ = 'customer_transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys (normalized)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    # Denormalized data (for historical accuracy)
    customer_name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    product_code = db.Column(db.String(50))
    product_name = db.Column(db.String(200))
    product_category = db.Column(db.String(100))
    
    unit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    total_cost = db.Column(db.Float)
    measure_unit = db.Column(db.String(20))
    
    def to_dict(self, include_relations=False, customer_data=None, product_data=None):
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'customer_name': self.customer_name,
            'city': self.city,
            'zipcode': self.zipcode,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'product_category': self.product_category,
            'unit_price': self.unit_price,
            'quantity': self.quantity,
            'total_cost': self.total_cost,
            'measure_unit': self.measure_unit
        }
        
        if include_relations:
            if customer_data:
                data['customer'] = customer_data
            if product_data:
                data['product'] = product_data
        
        return data
