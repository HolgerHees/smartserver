global:
  scrape_interval:     1m
  evaluation_interval: 1m

alerting:
  alertmanagers:
    - static_configs:
      - targets:
        - alertmanager:9093

rule_files:
{{RULE_FILES}}

scrape_configs:
{{SCRAPE_CONFIGS}}
