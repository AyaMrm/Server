-- Script pour nettoyer et recréer les tables MySQL
-- Copiez tout ce script et exécutez-le dans MySQL Workbench

-- 1. Supprimer les anciennes tables (dans l'ordre inverse des dépendances)
DROP TABLE IF EXISTS activity_log;
DROP TABLE IF EXISTS screenshots;
DROP TABLE IF EXISTS keylogs;
DROP TABLE IF EXISTS commands;
DROP TABLE IF EXISTS clients;

-- Message de confirmation
SELECT 'Tables supprimées avec succès!' as Status;
