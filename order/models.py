from datetime import datetime
from db import db


class Orders(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys (normalized)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    # Transaction data
    unit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    total_cost = db.Column(db.Float)
    
    def to_dict(self, include_relations=False, customer_data=None, product_data=None):
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'unit_price': self.unit_price,
            'quantity': self.quantity,
            'total_cost': self.total_cost
        }
        
        if include_relations:
            if customer_data:
                data['customer'] = customer_data
            if product_data:
                data['product'] = product_data
        
        return data
