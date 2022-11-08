from datetime import datetime, timedelta
import requests
import json


class Alertmanager():
    def buildAlert(notifyGroup, name, summary = None, startsAt = datetime.now(), labels = {}, url = None):
        alert = {}
        #fired_alert["status"] = "firing"
        alert["labels"] = { **{
            "notifyGroup": notifyGroup,
            "alertname": name
        }, **labels }
        alert["annotations"] = {}
        if summary is not None:
            alert["annotations"]["summary"] = summary

        alert["startsAt"] = startsAt.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

        if url is not None:
            alert["generatorURL"] = url

        return alert

    def buildResolve(fired_alerts, active_alerts):
        resolved_alerts = []
        for alert in active_alerts:
            #print(alert)

            if Alertmanager.find(alert, fired_alerts):
                continue

            resolved_alert = Alertmanager._buildResolve(alert)
            resolved_alerts.append(resolved_alert)
        return resolved_alerts

    def _buildResolve(alert):
        resolved_alert = {}
        #resolved_alert["status"] = "resolved"
        resolved_alert["labels"] = alert["labels"]

        endsAt = datetime.utcnow() - timedelta(seconds=1)
        resolved_alert["endsAt"] = endsAt.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

        return resolved_alert

    def find(alert, alerts):
        for _alert in alerts:
            if _alert["labels"] == alert["labels"]:
                return True
        return False

    def trigger(alertmanager_url, alerts):
        #headers = {
        #    'Accept': 'application/json',
        #    'Content-Type': 'text/plain'
        #}
        response = requests.post( alertmanager_url, data = json.dumps(alerts) )
        #response = requests.post( "http://openhab:8080/rest/items/State_Server/state", headers = headers, data = json.dumps(json) )
        if not (200 <= response.status_code < 300):
            response.raise_for_status()

    def fetch(alertmanager_url, notifyGroup):
        response = requests.get(alertmanager_url, timeout=5.0)
        response.raise_for_status()
        _alert_response = json.loads(response.content)
        if _alert_response["status"] == "success":
            _alertmanager_alerts = _alert_response["data"]
        else:
            _alertmanager_alerts = []

        alertmanager_alerts = []
        for alertmanager_alert in _alertmanager_alerts:
            #print(alert)

            if "notifyGroup" not in alertmanager_alert["labels"] or alertmanager_alert["labels"]["notifyGroup"] != notifyGroup:
                continue

            alertmanager_alerts.append(alertmanager_alert)

        return alertmanager_alerts
