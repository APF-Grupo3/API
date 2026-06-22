from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    fecha_ultima_compra = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password: str) -> None:
        """Genera y guarda el hash de la contraseña (nunca se guarda en texto plano)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Comprueba si la contraseña introducida coincide con el hash guardado."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Convierte el cliente a diccionario para serializar a JSON.

        Nunca incluye password_hash: ese campo no debe salir nunca en una respuesta.
        """
        return {
            "id": self.id,
            "email": self.email,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "pais": self.pais,
            "telefono": self.telefono,
            "activo": self.activo,
            "fecha_registro": self.fecha_registro.isoformat()
            if self.fecha_registro
            else None,
            "fecha_ultima_compra": self.fecha_ultima_compra.isoformat()
            if self.fecha_ultima_compra
            else None,
        }

    def __repr__(self) -> str:
        return f"<Cliente {self.email}>"
