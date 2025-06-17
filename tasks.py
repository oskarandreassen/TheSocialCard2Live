# tasks.py
from datetime import datetime, timedelta
from app import app, db          # importera app-instansen, inte create_app
from models import User

def purge_unconfirmed():
    """Tar bort alla konton som inte bekräftats efter 10 dagar."""
    cutoff = datetime.utcnow() - timedelta(days=10)
    with app.app_context():
        to_delete = User.query \
            .filter(User.email_confirmed == False, User.created_at < cutoff) \
            .all()
        count = len(to_delete)
        for u in to_delete:
            db.session.delete(u)
        db.session.commit()
        app.logger.info(f"Raderade {count} obekräftade konton.")
