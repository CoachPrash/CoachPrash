import os
from app import create_app

app = create_app()


@app.route('/health')
def health_check():
    from flask import jsonify
    return jsonify({"status": "healthy"}), 200


@app.route('/run-seed/<password>')
def run_seed_endpoint(password):
    from flask import jsonify
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_password or password != admin_password:
        return jsonify({"error": "unauthorized"}), 403
    from seed import run_seed
    run_seed()
    return jsonify({"status": "seeded"}), 200
