import secrets
from datetime import datetime, timedelta, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# Tiempo de vida del token de vinculación (15 minutos)
TOKEN_EXPIRY_MINUTES = 15


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
    # ── Telegram ──
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=True)
    telegram_linked_at = db.Column(db.DateTime, nullable=True)
    # ETFs a los que quiere suscribirse para recibir alertas
    telegram_tickers = db.Column(db.String(500), nullable=True)
    # Suscripción al resumen diario por Telegram
    telegram_suscrito = db.Column(db.Boolean, default=False, nullable=False)
    # ETFs favoritos del usuario (separados por comas)
    etfs_favoritos = db.Column(db.String(2000), nullable=True)

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
            "telegram_vinculado": self.telegram_chat_id is not None,
            "telegram_suscrito": bool(self.telegram_suscrito),
            "telegram_tickers": self.telegram_tickers,
            "etfs_favoritos": [t.strip() for t in self.etfs_favoritos.split(",") if t.strip()] if self.etfs_favoritos else [],
            "fecha_registro": self.fecha_registro.isoformat()
            if self.fecha_registro
            else None,
            "fecha_ultima_compra": self.fecha_ultima_compra.isoformat()
            if self.fecha_ultima_compra
            else None,
        }

    def __repr__(self) -> str:
        return f"<Cliente {self.email}>"


class TelegramToken(db.Model):
    """Token temporal para vincular un usuario con su chat de Telegram.

    Flujo:
    1. El usuario pide vincular → se genera un token único y se guarda aquí.
    2. El usuario abre t.me/Bot?start=TOKEN → Telegram envía /start TOKEN al bot.
    3. n8n recibe el update, extrae chat_id + token y llama a POST /vincular.
    4. El backend busca el token aquí, asocia el chat_id al cliente y borra el token.

    El token expira tras TOKEN_EXPIRY_MINUTES para evitar abusos.
    """
    __tablename__ = "telegram_tokens"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(db.DateTime, nullable=False)

    cliente = db.relationship("Cliente", backref=db.backref("telegram_tokens", lazy=True))

    @staticmethod
    def generate(cliente_id: int) -> "TelegramToken":
        """Crea un token seguro de 32 bytes (64 caracteres hex) con expiración."""
        now = datetime.now(timezone.utc)
        return TelegramToken(
            cliente_id=cliente_id,
            token=secrets.token_hex(32),
            created_at=now,
            expires_at=now + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        )

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires = self.expires_at.replace(tzinfo=None) if self.expires_at else now
        return now > expires


class Alerta(db.Model):
    """Alerta de precio/métrica asociada a un usuario."""
    __tablename__ = "alertas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    metrica = db.Column(db.String(50), nullable=False)
    condicion = db.Column(db.String(2), nullable=False)
    umbral = db.Column(db.Float, nullable=False)
    periodo = db.Column(db.String(10), nullable=False, default="1mo")
    creada_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Cliente", backref=db.backref("alertas", lazy=True))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticker": self.ticker,
            "metrica": self.metrica,
            "condicion": self.condicion,
            "umbral": self.umbral,
            "periodo": self.periodo,
            "creada_en": self.creada_en.isoformat() if self.creada_en else None,
        }


class AlertaLog(db.Model):
    """Registro histórico de alertas disparadas y notificadas."""
    __tablename__ = "alertas_log"

    id = db.Column(db.Integer, primary_key=True)
    alerta_id = db.Column(db.Integer, db.ForeignKey("alertas.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    metrica = db.Column(db.String(50), nullable=False)
    condicion = db.Column(db.String(2), nullable=False)
    umbral = db.Column(db.Float, nullable=False)
    valor_actual = db.Column(db.Float, nullable=False)
    periodo = db.Column(db.String(10), nullable=False)
    disparada_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    alerta = db.relationship("Alerta", backref=db.backref("logs", lazy=True))
    cliente = db.relationship("Cliente", backref=db.backref("alertas_log", lazy=True))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alerta_id": self.alerta_id,
            "cliente_id": self.cliente_id,
            "ticker": self.ticker,
            "metrica": self.metrica,
            "condicion": self.condicion,
            "umbral": self.umbral,
            "valor_actual": self.valor_actual,
            "periodo": self.periodo,
            "disparada_en": self.disparada_en.isoformat() if self.disparada_en else None,
        }
