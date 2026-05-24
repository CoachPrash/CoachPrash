import logging
import os
from app import create_app
from app.extensions import limiter, csrf

logger = logging.getLogger(__name__)

app = create_app()


@app.route('/health')
def health_check():
    from flask import jsonify
    return jsonify({"status": "healthy"}), 200


@app.route('/run-seed', methods=['POST'])
@csrf.exempt
@limiter.limit('1/minute')
def run_seed_endpoint():
    from flask import jsonify, request
    password = (request.json or {}).get('password', '') if request.is_json else request.form.get('password', '')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_password or password != admin_password:
        logger.warning('Unauthorized seed endpoint access attempt from %s', request.remote_addr)
        return jsonify({"error": "unauthorized"}), 403
    logger.info('Seed endpoint invoked')
    from seed import run_seed
    run_seed()
    return jsonify({"status": "seeded"}), 200


@app.route('/run-drop-all', methods=['POST'])
@csrf.exempt
@limiter.limit('1/minute')
def run_drop_all_endpoint():
    from flask import jsonify, request
    from app.extensions import db
    if os.environ.get('FLASK_ENV') == 'production':
        logger.warning('Drop-all endpoint blocked in production from %s', request.remote_addr)
        return jsonify({"error": "this endpoint is disabled in production"}), 403
    password = (request.json or {}).get('password', '') if request.is_json else request.form.get('password', '')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_password or password != admin_password:
        logger.warning('Unauthorized drop-all endpoint access attempt from %s', request.remote_addr)
        return jsonify({"error": "unauthorized"}), 403
    logger.warning('DROP ALL TABLES endpoint invoked — all data will be destroyed')
    db.drop_all()
    db.session.execute(db.text("DROP TABLE IF EXISTS alembic_version"))
    db.session.commit()
    logger.warning('All database tables dropped successfully')
    return jsonify({"status": "all tables dropped — redeploy to recreate via migration"}), 200
