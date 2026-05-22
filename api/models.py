class clientes(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_ultima_compra = db.Column(db.DateTime, default=datetime.utcnow)

    transacciones = db.relationship('transacciones', backref='cliente', lazy=True)
    portfolio = db.relationship('portfolio', backref='cliente', lazy=True)

    def to_dict(self):
        """ Convierte el objeto cliente a un diccionario para facilitar su serialización a JSON."""
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'pais': self.pais,
            'telefono': self.telefono,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.isoformat(),
            'fecha_ultima_compra': self.fecha_ultima_compra.isoformat(),
            'transacciones': [t.to_dict() for t in self.transacciones],
            'portfolio': [p.to_dict() for p in self.portfolio],
            'total_transacciones': len(self.transacciones),
            'total_acciones': len(self.portfolio) if hasattr(self, 'portfolio') else 0
        }
    
    def __repr__(self):
        return f"<Cliente {self.email}>"


# transacciones 

class transacciones(db.Model):
    id, clientes_id, monto, moneda, tipo, estado, descripcion, 
    # relaciones con un cliente 
    # estados posibles: pendiente, completada, cancelada
    # tipos posibles: compra, venta, deposito, retiro

# portfolio 

# auditoria

# Stock
