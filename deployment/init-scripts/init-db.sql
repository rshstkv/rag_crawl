-- Создание базы данных и пользователя
CREATE DATABASE rag_crawl;
CREATE USER rag_user WITH ENCRYPTED PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE rag_crawl TO rag_user;

-- Подключение к базе данных
\c rag_crawl

-- Предоставление прав на схему
GRANT ALL ON SCHEMA public TO rag_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO rag_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO rag_user;

-- Создание расширений если нужно
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 