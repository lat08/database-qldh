USE EduManagement;
GO

-- Dynamic query to SELECT * from all tables in the database
DECLARE @TableName NVARCHAR(128);
DECLARE @SQL NVARCHAR(MAX);

-- Cursor to iterate through all tables
DECLARE table_cursor CURSOR FOR
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

OPEN table_cursor;
FETCH NEXT FROM table_cursor INTO @TableName;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- Print table name for clarity
    PRINT '========================================';
    PRINT 'Table: ' + @TableName;
    PRINT '========================================';
    
    -- Build and execute SELECT query
    SET @SQL = 'SELECT * FROM ' + QUOTENAME(@TableName);
    EXEC sp_executesql @SQL;
    
    FETCH NEXT FROM table_cursor INTO @TableName;
END

CLOSE table_cursor;
DEALLOCATE table_cursor;