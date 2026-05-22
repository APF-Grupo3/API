-- tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    email VARCHAR(120) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    activo BOOLEAN DEFAULT 1,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- íNDICES DE CLIENTES
CREATE INDEX if NOT EXISTS idx_clientes_email ON clientes(email);
CREATE INDEX if NOT EXISTS idx_clientes_pais ON clientes(pais);
CREATE INDEX if NOT EXISTS idx_clientes_activo ON clientes(activo);

-- TABLA DE TRANSACCIONES
CREATE TABLE IF NOT EXISTS transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'USD',
    tipo VARCHAR(20) not null, -- pagado, rembolso, pendiente, transferencia
    estado VARCHAR(20) DEFAULT 'pendiente', -- pendiente, completada, fallida, cancelada
    descripcion VARCHAR(255),
    referencia_externa VARCHAR(100), 
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_completada TIMESTAMP,
    metadara TEXT, --JSON con información adicional

    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- índices de transacciones

-- tablas de auditoría logs

-- índeces de auditoría logs

-- tabla de acciones 

-- índices de acciones

-- tabla de portafolios de inversión por cliente 

-- índices de portafolios de inversión por cliente