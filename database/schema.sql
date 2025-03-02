CREATE TABLE user (
    id BIGINT PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    birthday DATE
);

CREATE TABLE companies (
    company_id BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    company_name VARCHAR NOT NULL,
    token DOUBLE PRECISION DEFAULT 0,
    company_phone_number VARCHAR NOT NULL,
    company_email VARCHAR,
    company_industry VARCHAR NOT NULL,
    company_country VARCHAR NOT NULL,
    company_city VARCHAR NOT NULL,
    company_address VARCHAR NOT NULL,
    company_description TEXT DEFAULT 'no description',
    company_image VARCHAR DEFAULT 'https://cjoykzgrtvlghogxzdjq.supabase.co/storage/v1/object/sign/immagine%20predefinita/22059000-no-immagine-a-disposizione-icona-vettoriale.jpg',
    company_website VARCHAR DEFAULT 'no link to website',
    status BOOLEAN NOT NULL,
    eth_address TEXT,
    co2_emission REAL NOT NULL DEFAULT 0,
    total_quantity INTEGER NOT NULL DEFAULT 0,
    co2_old REAL NOT NULL DEFAULT 0
);

CREATE TABLE company_employe (
    user_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    company_id BIGINT NOT NULL REFERENCES companies(company_id),
    company_admin BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE transport (
    id BIGINT PRIMARY KEY,
    date_delivery DATE NOT NULL,
    distance INTEGER NOT NULL,
    id_buyer BIGINT NOT NULL,
    id_seller BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id_transporter BIGINT NOT NULL,
    co2_emission REAL,
    id_product BIGINT NOT NULL
);

CREATE TABLE product_request (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id_buyer BIGINT NOT NULL,
    id_supplier BIGINT NOT NULL,
    id_raw_material BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    quantity_of_raw_material INTEGER NOT NULL,
    id_transporter BIGINT NOT NULL,
    transport_date DATE NOT NULL,
    distance_to_travel INTEGER NOT NULL,
    supplier_approve BOOLEAN DEFAULT FALSE,
    transporter_approve BOOLEAN DEFAULT FALSE,
    id_product BIGINT NOT NULL
);

CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    name VARCHAR NOT NULL,
    quantity INTEGER,
    description TEXT,
    company_id BIGINT REFERENCES companies(company_id),
    total_quantity INTEGER DEFAULT 0,
    co2_emission REAL DEFAULT 0
);

CREATE TABLE seller_products (
    id BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id_seller BIGINT NOT NULL,
    id_product BIGINT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_quantity INTEGER,
    co2_emission REAL
);

CREATE TABLE chain_products (
    serial_id BIGINT PRIMARY KEY,
    farmer BIGINT,
    transporter1 BIGINT,
    transporter2 BIGINT,
    transformer BIGINT,
    seller BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id BIGINT NOT NULL
);

CREATE TABLE user_logs (
    id BIGINT PRIMARY KEY,
    user_id TEXT,
    endpoint TEXT,
    method TEXT,
    path TEXT,
    status_code INTEGER,
    timestamp TIMESTAMPTZ,
    ip_address TEXT,
    user_agent TEXT,
    response_time DOUBLE PRECISION
);

CREATE TABLE notifications (
    id_notification BIGINT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    type VARCHAR NOT NULL,
    sender_email VARCHAR DEFAULT 'System',
    receiver_email VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    company_id BIGINT REFERENCES companies(company_id),
    product_request_id INTEGER,
    requested_token INTEGER,
    same_request BIGINT,
    sender_company_id BIGINT
);

CREATE TABLE recover_password_token (
    email VARCHAR PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    token VARCHAR NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE roles (
    user_id BIGINT PRIMARY KEY REFERENCES user(id),
    admin BOOLEAN NOT NULL
);