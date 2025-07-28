from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from config import Config
from models import Vehicle, MaintenanceLog, ScheduledMaintenance
from db import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

from sqlalchemy.exc import IntegrityError

@app.route('/')
def home():
    total_vehicles = Vehicle.query.count()
    total_logs = MaintenanceLog.query.count()
    vehicles_with_sched = db.session.query(Vehicle).join(ScheduledMaintenance).distinct().count()
    vehicles_without_sched = total_vehicles - vehicles_with_sched
    return render_template('home.html', total_vehicles=total_vehicles, total_logs=total_logs,
        vehicles_with_sched=vehicles_with_sched, vehicles_without_sched=vehicles_without_sched)

@app.route('/vehicles')
def list_vehicles():
    vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        try:
            vehicle = Vehicle(
                make=request.form['make'],
                model=request.form['model'],
                year=int(request.form['year']),
                license_plate=request.form['license_plate']
            )
            db.session.add(vehicle)
            db.session.commit()
            return redirect(url_for('list_vehicles'))
        except IntegrityError:
            db.session.rollback()
            return render_template('vehicle_add.html', error='License plate must be unique.')
    return render_template('vehicle_add.html')

@app.route('/vehicles/<int:vehicle_id>')
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    scheduled = ScheduledMaintenance.query.filter_by(vehicle_id=vehicle_id).order_by(ScheduledMaintenance.completed, ScheduledMaintenance.due_date, ScheduledMaintenance.due_odo).all()
    return render_template('vehicle_detail.html', vehicle=vehicle, scheduled=scheduled)

@app.route('/vehicles/<int:vehicle_id>/scheduled', methods=['GET', 'POST'])
def scheduled_maintenance(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        due_odo = request.form.get('due_odo') or None
        due_date = request.form.get('due_date') or None
        note = request.form.get('note')
        sched = ScheduledMaintenance(
            vehicle_id=vehicle.id,
            due_odo=int(due_odo) if due_odo else None,
            due_date=due_date,
            note=note
        )
        db.session.add(sched)
        db.session.commit()
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle.id))
    scheduled = ScheduledMaintenance.query.filter_by(vehicle_id=vehicle.id).order_by(ScheduledMaintenance.completed, ScheduledMaintenance.due_date, ScheduledMaintenance.due_odo).all()
    return render_template('scheduled_maintenance.html', vehicle=vehicle, scheduled=scheduled)

@app.route('/scheduled/<int:sched_id>/complete', methods=['POST'])
def complete_scheduled_maintenance(sched_id):
    sched = ScheduledMaintenance.query.get_or_404(sched_id)
    sched.completed = True
    db.session.commit()
    return redirect(url_for('vehicle_detail', vehicle_id=sched.vehicle_id))

@app.route('/vehicles/<int:vehicle_id>/maintenance-log', methods=['GET', 'POST'])
def maintenance_log(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        log = MaintenanceLog(
            vehicle_id=vehicle.id,
            cost=float(request.form['cost']),
            odo=int(request.form['odo']),
            date=request.form['date'],
            note=request.form['note']
        )
        db.session.add(log)
        db.session.commit()
    logs = MaintenanceLog.query.filter_by(vehicle_id=vehicle.id).all()
    return render_template('maintenance_log.html', vehicle=vehicle, logs=logs)

@app.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if request.method == 'POST':
        vehicle.make = request.form['make']
        vehicle.model = request.form['model']
        vehicle.year = int(request.form['year'])
        vehicle.license_plate = request.form['license_plate']
        try:
            db.session.commit()
            return redirect(url_for('view_vehicle', vehicle_id=vehicle.id))
        except IntegrityError:
            db.session.rollback()
            return render_template('vehicle_edit.html', vehicle=vehicle, error='License plate must be unique.')
    return render_template('vehicle_edit.html', vehicle=vehicle)

@app.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return redirect(url_for('list_vehicles'))

# --- RESTful API endpoints ---

@app.route('/api/vehicles', methods=['GET'])
def api_list_vehicles():
    vehicles = Vehicle.query.all()
    return jsonify([v.to_dict() for v in vehicles])

@app.route('/api/vehicles', methods=['POST'])
def api_add_vehicle():
    data = request.json
    vehicle = Vehicle(
        make=data['make'],
        model=data['model'],
        year=int(data['year']),
        license_plate=data['license_plate']
    )
    db.session.add(vehicle)
    db.session.commit()
    return jsonify(vehicle.to_dict()), 201

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET'])
def api_get_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return jsonify(vehicle.to_dict())

@app.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
def api_update_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.json
    vehicle.make = data['make']
    vehicle.model = data['model']
    vehicle.year = int(data['year'])
    vehicle.license_plate = data['license_plate']
    db.session.commit()
    return jsonify(vehicle.to_dict())

@app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
def api_delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return '', 204

@app.route('/api/vehicles/<int:vehicle_id>/maintenance', methods=['GET'])
def api_list_maintenance(vehicle_id):
    logs = MaintenanceLog.query.filter_by(vehicle_id=vehicle_id).all()
    return jsonify([log.to_dict() for log in logs])

@app.route('/api/vehicles/<int:vehicle_id>/maintenance', methods=['POST'])
def api_add_maintenance(vehicle_id):
    data = request.json
    log = MaintenanceLog(
        vehicle_id=vehicle_id,
        cost=float(data['cost']),
        odo=int(data['odo']),
        date=data['date'],
        note=data.get('note', '')
    )
    db.session.add(log)
    db.session.commit()
    return jsonify(log.to_dict()), 201

@app.route('/api/maintenance/<int:log_id>', methods=['GET'])
def api_get_maintenance(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    return jsonify(log.to_dict())

@app.route('/api/maintenance/<int:log_id>', methods=['PUT'])
def api_update_maintenance(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    data = request.json
    log.cost = float(data['cost'])
    log.odo = int(data['odo'])
    log.date = data['date']
    log.note = data.get('note', '')
    db.session.commit()
    return jsonify(log.to_dict())

@app.route('/api/maintenance/<int:log_id>', methods=['DELETE'])
def api_delete_maintenance(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return '', 204


import click

@app.cli.command('db-create')
def db_create():
    db.create_all()
    print('Database created!')

@app.cli.command('db-drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')

@app.cli.command('db-seed')
def db_seed():
    v1 = Vehicle(make='Toyota', model='Corolla', year=2018, license_plate='ABC123')
    v2 = Vehicle(make='Honda', model='Civic', year=2020, license_plate='XYZ789')
    db.session.add_all([v1, v2])
    db.session.commit()
    print('Database seeded!')

if __name__ == '__main__':
    app.run(debug=True)
