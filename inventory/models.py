from db import db


class Storage(db.Model):
    __tablename__ = 'storages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    
    def to_dict(self, include_product=False, product_data=None):
        data = {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity
        }
        
        if include_product and product_data:
            data['product'] = product_data
        
        return data
