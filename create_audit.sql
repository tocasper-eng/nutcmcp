-- Step 1: 建立 Audit 目錄
EXEC xp_cmdshell 'if not exist "C:\SQLAudit\nutc_audit" mkdir "C:\SQLAudit\nutc_audit"';
GO

-- Step 2: 若已存在先移除舊的
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = 'nutc_audit_spec')
BEGIN
    ALTER SERVER AUDIT SPECIFICATION [nutc_audit_spec] WITH (STATE = OFF);
    DROP SERVER AUDIT SPECIFICATION [nutc_audit_spec];
END
GO

IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = 'nutc_audit')
BEGIN
    ALTER SERVER AUDIT [nutc_audit] WITH (STATE = OFF);
    DROP SERVER AUDIT [nutc_audit];
END
GO

-- Step 3: 建立 Server Audit（寫入檔案）
CREATE SERVER AUDIT [nutc_audit]
TO FILE (
    FILEPATH = N'C:\SQLAudit\nutc_audit\',
    MAXSIZE = 100 MB,
    MAX_ROLLOVER_FILES = 20,
    RESERVE_DISK_SPACE = OFF
)
WITH (
    QUEUE_DELAY = 1000,
    ON_FAILURE = CONTINUE,
    AUDIT_GUID = NEWID()
)
WHERE server_principal_name LIKE 'nutc%';
GO

ALTER SERVER AUDIT [nutc_audit] WITH (STATE = ON);
GO

-- Step 4: 建立 Server Audit Specification（危險動作清單）
CREATE SERVER AUDIT SPECIFICATION [nutc_audit_spec]
FOR SERVER AUDIT [nutc_audit]
ADD (DATABASE_CHANGE_GROUP),             -- CREATE/ALTER/DROP DATABASE
ADD (DATABASE_OBJECT_CHANGE_GROUP),      -- CREATE/ALTER/DROP TABLE, VIEW, PROC...
ADD (SCHEMA_OBJECT_CHANGE_GROUP),        -- DDL in schema (TABLE, INDEX...)
ADD (DATABASE_PRINCIPAL_CHANGE_GROUP),   -- CREATE/ALTER/DROP USER, ROLE
ADD (SERVER_PRINCIPAL_CHANGE_GROUP),     -- CREATE/ALTER/DROP LOGIN
ADD (SERVER_PERMISSION_CHANGE_GROUP),    -- GRANT/REVOKE/DENY at server
ADD (DATABASE_PERMISSION_CHANGE_GROUP),  -- GRANT/REVOKE/DENY at database
ADD (BACKUP_RESTORE_GROUP),              -- BACKUP / RESTORE
ADD (DBCC_GROUP),                        -- DBCC 命令
ADD (LOGIN_CHANGE_PASSWORD_GROUP),       -- 修改密碼
ADD (FAILED_LOGIN_GROUP)                 -- 登入失敗
WITH (STATE = ON);
GO

PRINT '=== Audit 建立完成 ===';
SELECT name, is_state_enabled, audit_file_path
FROM sys.server_audits
WHERE name = 'nutc_audit';
GO
