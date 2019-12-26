SELECT * INTO "{{database}}"."1s_for_7d".:MEASUREMENT FROM "{{database}}"."autogen"./.*/ WHERE time > now() - 7d GROUP BY *       
SELECT * INTO "{{database}}"."10s_for_21d".:MEASUREMENT FROM "{{database}}"."autogen"./.*/ WHERE time > now() - 21d GROUP BY *       
SELECT * INTO "{{database}}"."30s_for_90d".:MEASUREMENT FROM "{{database}}"."autogen"./.*/ WHERE time > now() - 90d GROUP BY *       
SELECT * INTO "{{database}}"."2m_for_180d".:MEASUREMENT FROM "{{database}}"."autogen"./.*/ WHERE time > now() - 180d GROUP BY *       
SELECT * INTO "{{database}}"."5m_for_360d".:MEASUREMENT FROM "{{database}}"."autogen"./.*/ WHERE time > now() - 360d GROUP BY *       
SELECT * INTO "{{database}}"."15m_for_inf".:MEASUREMENT FROM "{{database}}"."autogen"./.*/ GROUP BY *       