-- 重置 nutc00~nutc30 密碼為 Nutc@2026
DECLARE @i INT = 0;
WHILE @i <= 30
BEGIN
    DECLARE @name NVARCHAR(20) = 'nutc' + RIGHT('00' + CAST(@i AS VARCHAR), 2);
    DECLARE @sql NVARCHAR(200) = 'ALTER LOGIN [' + @name + '] WITH PASSWORD = N''Nutc@2026'', CHECK_POLICY = OFF';
    EXEC sp_executesql @sql;
    PRINT @name + ' 密碼已重置';
    SET @i = @i + 1;
END
PRINT '=== 全部重置完成 ===';
