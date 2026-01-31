from db import db


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    city = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'zipcode': self.zipcode,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email
        }
