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

    def buildAlertExpire(fired_alerts, active_alerts):
        resolved_alerts = []
        for alert in active_alerts:
            #print(alert)

            if Alertmanager.findAlert(alert, fired_alerts):
                continue

            resolved_alert = Alertmanager._buildAlertExpire(alert)
            resolved_alerts.append(resolved_alert)
        return resolved_alerts

    def _buildAlertExpire(alert):
        resolved_alert = {}
        #resolved_alert["status"] = "resolved"
        resolved_alert["labels"] = alert["labels"]

        endsAt = datetime.utcnow() - timedelta(seconds=1)
        resolved_alert["endsAt"] = endsAt.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

        return resolved_alert

    def findAlert(alert, alerts):
        for _alert in alerts:
            if _alert["labels"] == alert["labels"]:
                return True
        return False

    def triggerAlerts(alertmanager_base_url, alerts):
        #headers = {
        #    'Accept': 'application/json',
        #    'Content-Type': 'text/plain'
        #}
        response = requests.post( "{}api/v1/alerts".format(alertmanager_base_url), data = json.dumps(alerts) )
        #response = requests.post( "http://openhab:8080/rest/items/State_Server/state", headers = headers, data = json.dumps(json) )
        if not (200 <= response.status_code < 300):
            response.raise_for_status()

    def fetchAlerts(alertmanager_base_url, notifyGroup):
        response = requests.get("{}api/v1/alerts".format(alertmanager_base_url), timeout=5.0)
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

    def buildSilence( matchers, name):
        silence = {}

        silence["matchers"] = matchers
        silence["createdBy"] = "api"
        silence["comment"] = name
        #silence["status"] = { "state": "active" }

        startsAt = datetime.utcnow()
        silence["startsAt"] = startsAt.isoformat()#.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
        silence["endsAt"] = "2999-01-01T01:01:01.000000000Z"

        return silence

    def findSilence(name, matchers, silences):
        for silence in silences:
            if silence["comment"] == name:
                pairs = zip(matchers, silence["matchers"])
                has_differences = any(x != y for x, y in pairs)
                if not has_differences:
                    return silence
        return None

    def triggerSilence(alertmanager_base_url, silence):
        #headers = {
        #    'Accept': 'application/json',
        #    'Content-Type': 'text/plain'
        #}
        response = requests.post( "{}api/v2/silences".format(alertmanager_base_url), json = silence )
        #response = requests.post( "http://openhab:8080/rest/items/State_Server/state", headers = headers, data = json.dumps(json) )
        if not (200 <= response.status_code < 300):
            response.raise_for_status()

    def deleteSilence(alertmanager_base_url, id):
        #headers = {
        #    'Accept': 'application/json',
        #    'Content-Type': 'text/plain'
        #}
        response = requests.delete( "{}api/v2/silence/{}".format(alertmanager_base_url, id))
        #response = requests.post( "http://openhab:8080/rest/items/State_Server/state", headers = headers, data = json.dumps(json) )
        if not (200 <= response.status_code < 300):
            response.raise_for_status()

    def fetchSilences(alertmanager_base_url):
        response = requests.get("{}api/v1/silences".format(alertmanager_base_url), timeout=5.0)
        response.raise_for_status()
        _alert_response = json.loads(response.content)
        if _alert_response["status"] == "success":
            _alertmanager_silences = _alert_response["data"]
        else:
            _alertmanager_silences = []

        alertmanager_silences = []
        for alertmanager_silence in _alertmanager_silences:
            #print(alert)

            if alertmanager_silence["createdBy"] != "api" or alertmanager_silence["status"]["state"] != "active":
                continue

            alertmanager_silences.append(alertmanager_silence)

        return alertmanager_silences

