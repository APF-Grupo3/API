-- tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    email VARCHAR(120) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT 1,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Telegram
    telegram_chat_id VARCHAR(50) UNIQUE,
    telegram_linked_at DATETIME,
    telegram_tickers VARCHAR(500),
    telegram_suscrito BOOLEAN NOT NULL DEFAULT 0,
    -- Favoritos
    etfs_favoritos VARCHAR(2000)
);

-- íNDICES DE CLIENTES
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
CREATE INDEX IF NOT EXISTS idx_clientes_pais ON clientes(pais);
CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo);
CREATE INDEX IF NOT EXISTS idx_clientes_telegram ON clientes(telegram_chat_id);

-- TABLA DE TOKENS TEMPORALES PARA VINCULAR TELEGRAM
CREATE TABLE IF NOT EXISTS telegram_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- TABLA DE ALERTAS
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    metrica VARCHAR(50) NOT NULL,
    condicion VARCHAR(2) NOT NULL,       -- '>' o '<'
    umbral FLOAT NOT NULL,
    periodo VARCHAR(10) NOT NULL DEFAULT '1mo',  -- 1d, 5d, 1wk, 1mo, 3mo, 6mo, 1y
    creada_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE INDEX IF NOT EXISTS idx_alertas_cliente ON alertas(cliente_id);

-- TABLA DE LOG DE ALERTAS DISPARADAS
CREATE TABLE IF NOT EXISTS alertas_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alerta_id INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    metrica VARCHAR(50) NOT NULL,
    condicion VARCHAR(2) NOT NULL,
    umbral FLOAT NOT NULL,
    valor_actual FLOAT NOT NULL,
    periodo VARCHAR(10) NOT NULL,
    disparada_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alerta_id) REFERENCES alertas(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE INDEX IF NOT EXISTS idx_alertas_log_cliente ON alertas_log(cliente_id);
CREATE INDEX IF NOT EXISTS idx_alertas_log_fecha ON alertas_log(disparada_en);

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
