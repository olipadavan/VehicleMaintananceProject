from db import db

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    license_plate = db.Column(db.String(32), nullable=False, unique=True)
    maintenance_logs = db.relationship('MaintenanceLog', backref='vehicle', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'license_plate': self.license_plate,
            'maintenance_logs': [log.to_dict() for log in self.maintenance_logs],
        }

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    odo = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(32), nullable=False)
    note = db.Column(db.String(256))

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'cost': self.cost,
            'odo': self.odo,
            'date': self.date,
            'note': self.note,
        }

class ScheduledMaintenance(db.Model):
    __tablename__ = 'scheduled_maintenance'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    due_odo = db.Column(db.Integer, nullable=True)
    due_date = db.Column(db.String(32), nullable=True)
    note = db.Column(db.String(256))
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    vehicle = db.relationship('Vehicle', backref=db.backref('scheduled_maintenance', cascade='all, delete-orphan', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'due_odo': self.due_odo,
            'due_date': self.due_date,
            'note': self.note,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
