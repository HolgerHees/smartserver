#!/usr/bin/python3

import yaml
import re

from smartserver.alertmanager import Alertmanager

ALERTMANAGER_BASE_URL = "http://alertmanager:9093/"
CONFIG_YML = "{{global_etc}}alertmanager/silent_alerts.yml"

alertmanager_silences = Alertmanager.fetchSilences(ALERTMANAGER_BASE_URL)

with open(CONFIG_YML, "r") as stream:
    config = yaml.load(stream, Loader=yaml.BaseLoader)
    #  {
    #          "name": "alername1",
    #          "value": ".*",
    #          "isRegex": true
    #        }
    #      ],

    for silence_config in config["silent_alerts"]:
        matchers = []
        for matcher_config in silence_config["matchers"]:
            m = re.match("([A-Za-z0-9]*)([=!~]*)\"(.*)\"", matcher_config)

            isRegex = "~" in m.group(2)
            isEqual = "!" not in m.group(2)

            matcher = {
                "name": m.group(1),
                "value": m.group(3),
                "isRegex": isRegex,
                "isEqual": isEqual
            }
            matchers.append(matcher)

        silence = Alertmanager.findSilence(silence_config["name"], matchers, alertmanager_silences)
        if silence is not None:
            alertmanager_silences.remove(silence)
        else:
            print("Create silence {}".format(silence_config["name"]))
            silence = Alertmanager.buildSilence(matchers, silence_config["name"])
            Alertmanager.triggerSilence(ALERTMANAGER_BASE_URL, silence)

for alertmanager_silence in alertmanager_silences:
    print("Expire silence {} - {}".format(alertmanager_silence["comment"], alertmanager_silence["id"]))
    Alertmanager.deleteSilence(ALERTMANAGER_BASE_URL, alertmanager_silence["id"])

