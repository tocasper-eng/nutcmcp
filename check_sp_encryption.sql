-- 查詢沒有加密的 Stored Procedure（三個資料庫）
SELECT 'casper' AS [資料庫], COUNT(*) AS [未加密 SP 數量]
FROM casper.sys.objects
WHERE type = 'P'
  AND OBJECTPROPERTY(object_id, 'IsEncrypted') = 0
UNION ALL
SELECT 'chjer', COUNT(*)
FROM chjer.sys.objects
WHERE type = 'P'
  AND OBJECTPROPERTY(object_id, 'IsEncrypted') = 0
UNION ALL
SELECT 'jet', COUNT(*)
FROM jet.sys.objects
WHERE type = 'P'
  AND OBJECTPROPERTY(object_id, 'IsEncrypted') = 0;

-- 詳細清單（以 casper 為例，其他資料庫改 USE）
-- USE casper;
SELECT
    DB_NAME()                AS [資料庫],
    SCHEMA_NAME(schema_id)  AS [結構描述],
    name                    AS [SP 名稱],
    create_date             AS [建立時間],
    modify_date             AS [修改時間]
FROM sys.objects
WHERE type = 'P'
  AND OBJECTPROPERTY(object_id, 'IsEncrypted') = 0
ORDER BY SCHEMA_NAME(schema_id), name;
