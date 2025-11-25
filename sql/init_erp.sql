-- init_erp.sql
-- Criação da tabela de impostos simulada
CREATE TABLE IF NOT EXISTS category_taxes (
    category_name VARCHAR(50) PRIMARY KEY,
    tax_rate DECIMAL(4, 2)
);
-- Inserção de dados simulados
INSERT INTO category_taxes (category_name, tax_rate)
VALUES ('beleza_saude', 0.10),
    ('informatica_acessorios', 0.15),
    ('automotivo', 0.20),
    ('cama_mesa_banho', 0.12),
    ('moveis_decoracao', 0.18),
    ('esporte_lazer', 0.15),
    ('perfumaria', 0.25),
    ('utilidades_domesticas', 0.10) ON CONFLICT (category_name) DO NOTHING;