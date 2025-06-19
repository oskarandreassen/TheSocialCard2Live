# tasks.py
from datetime import datetime, timedelta
from app import app, db          # importera app-instansen, inte create_app
from models import User


def purge_unconfirmed(include_recent: bool = False) -> int:
    """Tar bort alla konton som inte bekräftats.

    Om ``include_recent`` är ``False`` tas bara konton som är mer än
    tio dagar gamla bort. När ``include_recent`` är ``True`` raderas även
    nyare konton, vilket används för manuell rensning via admin.
    """
    cutoff = datetime.utcnow() - timedelta(days=10)
    with app.app_context():
        query = User.query.filter(User.email_confirmed == False)
        if not include_recent:
            query = query.filter(User.created_at < cutoff)
        to_delete = query.all()
        count = len(to_delete)
        for u in to_delete:
            db.session.delete(u)
        db.session.commit()
        app.logger.info(f"Raderade {count} obekräftade konton.")
        return count