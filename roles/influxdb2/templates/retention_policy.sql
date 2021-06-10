DROP RETENTION POLICY "config" ON "{{database}}";
CREATE RETENTION POLICY "config" ON {{database}} DURATION INF REPLICATION 1;

ALTER RETENTION POLICY "autogen" ON {{database}} DURATION 14d REPLICATION 1 DEFAULT;

CREATE RETENTION POLICY "10s_for_28d" ON {{database}} DURATION 28d REPLICATION 1;
DROP CONTINUOUS QUERY "cq_10s_for_28d" ON "{{database}}";
CREATE CONTINUOUS QUERY "cq_10s_for_28d" ON "{{database}}" 
RESAMPLE EVERY 30s FOR 40s
BEGIN 
    SELECT mean(value) as "value" INTO "{{database}}"."10s_for_28d".:MEASUREMENT FROM /.*/ GROUP BY time(10s)
END;

CREATE RETENTION POLICY "30s_for_90d" ON {{database}} DURATION 90d REPLICATION 1;
DROP CONTINUOUS QUERY "cq_30s_for_90d" ON "{{database}}";
CREATE CONTINUOUS QUERY "cq_30s_for_90d" ON "{{database}}" 
RESAMPLE EVERY 90s FOR 120s
BEGIN 
    SELECT mean(value) as "value" INTO "{{database}}"."30s_for_90d".:MEASUREMENT FROM /.*/ GROUP BY time(30s)
END;

CREATE RETENTION POLICY "2m_for_180d" ON {{database}} DURATION 180d REPLICATION 1;
DROP CONTINUOUS QUERY "cq_2m_for_180d" ON "{{database}}";
CREATE CONTINUOUS QUERY "cq_2m_for_180d" ON "{{database}}" 
RESAMPLE EVERY 6m FOR 8m
BEGIN 
    SELECT mean(value) as "value" INTO "{{database}}"."2m_for_180d".:MEASUREMENT FROM /.*/ GROUP BY time(2m) 
END;

CREATE RETENTION POLICY "5m_for_360d" ON {{database}} DURATION 360d REPLICATION 1;
DROP CONTINUOUS QUERY "cq_5m_for_360d" ON "{{database}}";
CREATE CONTINUOUS QUERY "cq_5m_for_360d" ON "{{database}}" 
RESAMPLE EVERY 15m FOR 20m
BEGIN 
    SELECT mean(value) as "value" INTO "{{database}}"."5m_for_360d".:MEASUREMENT FROM /.*/ GROUP BY time(5m)
END;

CREATE RETENTION POLICY "15m_for_inf" ON {{database}} DURATION INF REPLICATION 1;
DROP CONTINUOUS QUERY "cq_15m_for_inf" ON "{{database}}";
CREATE CONTINUOUS QUERY "cq_15m_for_inf" ON "{{database}}" 
RESAMPLE EVERY 45m FOR 60m
BEGIN 
    SELECT mean(value) as "value" INTO "{{database}}"."15m_for_inf".:MEASUREMENT FROM /.*/ GROUP BY time(15m)
END;


