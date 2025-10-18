USE EduManagement;
GO

-- Disable all constraints to avoid dependency errors
EXEC sp_MSforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT ALL"

-- Drop all foreign key constraints
DECLARE @sql NVARCHAR(MAX) = ''
SELECT @sql += 'ALTER TABLE [' + TABLE_SCHEMA + '].[' + TABLE_NAME + '] DROP CONSTRAINT [' + CONSTRAINT_NAME + '];'
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE CONSTRAINT_TYPE = 'FOREIGN KEY'
EXEC sp_executesql @sql

-- Drop all tables
SET @sql = ''
SELECT @sql += 'DROP TABLE [' + TABLE_SCHEMA + '].[' + TABLE_NAME + '];'
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
EXEC sp_executesql @sql

-- Drop all stored procedures (user-defined only)
DECLARE @procSql NVARCHAR(MAX) = '';
SELECT @procSql += 'DROP PROCEDURE [' + ROUTINE_SCHEMA + '].[' + ROUTINE_NAME + '];' + CHAR(13)
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE'
AND ROUTINE_SCHEMA != 'sys'
AND ROUTINE_NAME NOT LIKE 'sp_%'
AND ROUTINE_NAME NOT LIKE 'fn_%'
AND ROUTINE_NAME NOT LIKE 'dt_%';
EXEC sp_executesql @procSql;

-- Drop all user-defined functions
DECLARE @funcSql NVARCHAR(MAX) = '';
SELECT @funcSql += 'DROP FUNCTION [' + ROUTINE_SCHEMA + '].[' + ROUTINE_NAME + '];' + CHAR(13)
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'FUNCTION'
AND ROUTINE_SCHEMA != 'sys'
AND ROUTINE_NAME NOT LIKE 'sp_%'
AND ROUTINE_NAME NOT LIKE 'fn_%'
AND ROUTINE_NAME NOT LIKE 'dt_%';
EXEC sp_executesql @funcSql;

-- Drop all views
DECLARE @viewSql NVARCHAR(MAX) = '';
SELECT @viewSql += 'DROP VIEW [' + TABLE_SCHEMA + '].[' + TABLE_NAME + '];' + CHAR(13)
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA != 'sys';
EXEC sp_executesql @viewSql;