from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, redirect, url_for, render_template
from flask_apscheduler import APScheduler

class Config(object):
    JOBS = [
        {
            'id': 'send_reminders',
            'func': 'app:send_reminders',
            'trigger': 'interval',
            'seconds': 10
        }
    ]

app = Flask(__name__)

app.config.from_object(Config)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
scheduler = APScheduler()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

def send_reminders():
    with app.app_context():
        print("Reminder check initiated")
        upcoming_tasks = Task.query.filter(Task.due_date <= datetime.now(), Task.is_completed == False).all()
        for task in upcoming_tasks:
            Task.is_completed = True
            send_reminder_log(task)
            db.session.commit()

def send_reminder_log(task):
    message = 'Task Reminder: {}\nDescription: {}\nDue Date: {}'.format(task.task_name, task.description, task.due_date)
    print(message)

@app.route('/tasks', methods=['GET', 'POST'])
def get_tasks():
    if request.method == 'POST':
        task_name = request.form['task_name']
        description = request.form['description']
        category = request.form['category']
        due_date_str = request.form['due_date']
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        task = Task(task_name=task_name, description=description, category=category, due_date=due_date)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('get_tasks'))
    else:
        category = request.args.get('category')
        due_date_str = request.args.get('due_date')

        if category:
            tasks = Task.query.filter_by(category=category).all()
        elif due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            tasks = Task.query.filter_by(due_date=due_date).all()
        else:
            tasks = Task.query.all()

        return render_template('tasks.html', tasks=tasks)

@app.route('/tasks/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if request.method == 'POST':
        task = Task.query.get(task_id)
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('get_tasks'))

if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True)
