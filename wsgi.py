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
    if not admin_password:
        return jsonify({"error": "ADMIN_PASSWORD env var is not set or empty", "hint": "set it in Railway Variables"}), 403
    if password != admin_password:
        return jsonify({"error": "password mismatch", "password_length": len(password), "expected_length": len(admin_password)}), 403
    from seed import run_seed
    run_seed()
    return jsonify({"status": "seeded"}), 200
