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


@app.route('/run-migrate/<password>')
def run_migrate_endpoint(password):
    from flask import jsonify
    from app.extensions import db
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_password or password != admin_password:
        return jsonify({"error": "unauthorized"}), 403
    results = []
    migrations = [
        ("auth_provider", "ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'local'"),
        ("google_id", "ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE"),
        ("password_hash_nullable", "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"),
    ]
    for name, sql in migrations:
        try:
            db.session.execute(db.text(sql))
            results.append({"migration": name, "status": "applied"})
        except Exception as e:
            db.session.rollback()
            if 'already exists' in str(e) or 'duplicate column' in str(e).lower():
                results.append({"migration": name, "status": "already applied"})
            else:
                results.append({"migration": name, "status": f"error: {e}"})
    db.session.commit()
    return jsonify({"results": results}), 200
