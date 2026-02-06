from datetime import datetime
from db import db


class Procurements(db.Model):
    __tablename__ = 'procurements'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys (normalized)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, index=True)
    
    # Transaction data
    quantity = db.Column(db.Integer)
    total_cost = db.Column(db.Float)
    
    def to_dict(self, include_relations=False, supplier_data=None, product_data=None):
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'supplier_id': self.supplier_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_cost': self.total_cost
        }
        
        # Get unit_price from product data if available
        if product_data and 'price_buy' in product_data:
            data['unit_price'] = product_data['price_buy']
        
        if include_relations:
            if supplier_data:
                data['supplier'] = supplier_data
            if product_data:
                data['product'] = product_data
        
        return data
