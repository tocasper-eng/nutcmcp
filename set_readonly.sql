-- ================================================
-- 將 nutc00~nutc30 設定為 casper / chjer / jet
-- 三個資料庫的唯讀帳號
-- ================================================

DECLARE @i INT;
DECLARE @name NVARCHAR(20);
DECLARE @sql NVARCHAR(500);
DECLARE @db NVARCHAR(128);
DECLARE @databases TABLE (dbname NVARCHAR(128));

INSERT INTO @databases VALUES ('casper'), ('chjer'), ('jet');

DECLARE db_cursor CURSOR FOR SELECT dbname FROM @databases;
OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @db;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @i = 0;
    WHILE @i <= 30
    BEGIN
        SET @name = 'nutc' + RIGHT('00' + CAST(@i AS VARCHAR), 2);

        -- 1. 建立 User（若尚未存在）
        SET @sql = N'
            USE [' + @db + N'];
            IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N''' + @name + N''')
                CREATE USER [' + @name + N'] FOR LOGIN [' + @name + N'];';
        EXEC sp_executesql @sql;

        -- 2. 加入 db_datareader
        SET @sql = N'
            USE [' + @db + N'];
            ALTER ROLE db_datareader ADD MEMBER [' + @name + N'];';
        EXEC sp_executesql @sql;

        -- 3. 從 db_datawriter 移除（確保無寫入權限）
        SET @sql = N'
            USE [' + @db + N'];
            IF EXISTS (
                SELECT 1 FROM sys.database_role_members rm
                JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.database_principals u ON rm.member_principal_id = u.principal_id
                WHERE r.name = ''db_datawriter'' AND u.name = N''' + @name + N'''
            )
                ALTER ROLE db_datawriter DROP MEMBER [' + @name + N'];';
        EXEC sp_executesql @sql;

        PRINT '[' + @db + '] ' + @name + ' -> 唯讀設定完成';
        SET @i = @i + 1;
    END

    FETCH NEXT FROM db_cursor INTO @db;
END

CLOSE db_cursor;
DEALLOCATE db_cursor;

PRINT '=== 全部設定完成 ===';

-- ================================================
-- 驗證：查詢三個資料庫的角色設定
-- ================================================
PRINT '--- casper ---';
SELECT u.name AS [帳號], r.name AS [角色]
FROM casper.sys.database_role_members rm
JOIN casper.sys.database_principals r ON rm.role_principal_id = r.principal_id
JOIN casper.sys.database_principals u ON rm.member_principal_id = u.principal_id
WHERE u.name LIKE 'nutc%'
ORDER BY u.name, r.name;

PRINT '--- chjer ---';
SELECT u.name AS [帳號], r.name AS [角色]
FROM chjer.sys.database_role_members rm
JOIN chjer.sys.database_principals r ON rm.role_principal_id = r.principal_id
JOIN chjer.sys.database_principals u ON rm.member_principal_id = u.principal_id
WHERE u.name LIKE 'nutc%'
ORDER BY u.name, r.name;

PRINT '--- jet ---';
SELECT u.name AS [帳號], r.name AS [角色]
FROM jet.sys.database_role_members rm
JOIN jet.sys.database_principals r ON rm.role_principal_id = r.principal_id
JOIN jet.sys.database_principals u ON rm.member_principal_id = u.principal_id
WHERE u.name LIKE 'nutc%'
ORDER BY u.name, r.name;
