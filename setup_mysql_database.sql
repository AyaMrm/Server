-- Script de configuration MySQL pour le serveur C2
-- Exécutez ce script avec : mysql -u root -p < setup_mysql_database.sql

-- Créer la base de données
CREATE DATABASE IF NOT EXISTS c2_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Créer l'utilisateur (supprimer d'abord s'il existe)
DROP USER IF EXISTS 'c2_user'@'localhost';
CREATE USER 'c2_user'@'localhost' IDENTIFIED BY 'VotreMotDePasse123!';

-- Donner tous les privilèges
GRANT ALL PRIVILEGES ON c2_database.* TO 'c2_user'@'localhost';

-- Appliquer les changements
FLUSH PRIVILEGES;

-- Afficher les bases de données
SHOW DATABASES;

-- Afficher les utilisateurs
SELECT User, Host FROM mysql.user WHERE User = 'c2_user';
