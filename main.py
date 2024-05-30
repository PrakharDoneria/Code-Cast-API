from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
port = 3000

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

db_url = os.getenv('COCKROACHDB_URL')

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Code(Base):
    __tablename__ = 'codes'

    uid = Column(String, primary_key=True)
    code = Column(String)
    created_at = Column(DateTime, default=func.now())


Base.metadata.create_all(engine)

def delete_old_records():
    session = Session()
    try:
        cutoff_date = datetime.now() - timedelta(days=30)
        session.query(Code).filter(Code.created_at < cutoff_date).delete()
        session.commit()
    except Exception as e:
        print('Error deleting old records:', e)
    finally:
        session.close()

scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_records, 'interval', days=1)
scheduler.start()

@app.route('/create', methods=['GET'])
def create():
    uid = request.args.get('uid')
    code = request.args.get('code')

    try:
        session = Session()
        existing_record = session.query(Code).filter_by(uid=uid).first()
        if existing_record:
            existing_record.code = code
            existing_record.created_at = datetime.now()
            session.commit()
            return jsonify({'status': 'success', 'message': 'Record updated successfully'})
        else:
            new_record = Code(uid=uid, code=code)
            session.add(new_record)
            session.commit()
            return jsonify({'status': 'success', 'message': 'Record created successfully'})
    except Exception as e:
        print('Error creating/updating record:', e)
        return jsonify({'status': 'error', 'message': 'Failed to create/update record'}), 500
    finally:
        session.close()

@app.route('/delete', methods=['GET'])
def delete():
    uid = request.args.get('uid')

    try:
        session = Session()
        record_to_delete = session.query(Code).filter_by(uid=uid).first()
        if record_to_delete:
            session.delete(record_to_delete)
            session.commit()
        return jsonify({'code': 200})
    except Exception as e:
        print('Error deleting record:', e)
        return jsonify({'error': 'Failed to delete record'}), 500
    finally:
        session.close()

@app.route('/cast', methods=['GET'])
def cast():
    uid = request.args.get('uid')

    try:
        session = Session()
        result = session.query(Code).filter_by(uid=uid).first()
        if result:
            return jsonify({'code': 200, 'data': result.code})
        else:
            return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        print('Error retrieving record:', e)
        return jsonify({'error': 'Failed to retrieve record'}), 500
    finally:
        session.close()

@app.route('/preview', methods=['GET'])
def preview():
    uid = request.args.get('uid')

    try:
        session = Session()
        result = session.query(Code).filter_by(uid=uid).first()
        if result:
            return result.code
        else:
            return jsonify({'error': 'Record not found'}), 404
    except Exception as e:
        print('Error retrieving record for preview:', e)
        return jsonify({'error': 'Failed to retrieve record for preview'}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(port=port)
