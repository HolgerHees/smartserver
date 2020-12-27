# -*- coding: utf-8 -*-
from color_config import ColorConfig

SemanticConfig = {
    "i18n": {
        "nothing_found": u"Ich habe '{term}' nicht verstanden",
        "no_equipment_found_in_phrase": u"Ich habe das Gerät in '{term}' nicht erkannt",
        "no_cmd_found_in_phrase": u"Ich habe die Aktion in '{term}' nicht erkannt",
        "no_supported_cmd_in_phrase": u"Die Aktion wird für das Gerät in '{term}' nicht unterstützt",
        "more_results": u"und {count} weitere Ergebnisse.",
        "message_join_separator": u" und ",
        "ok_message": "ok"
    },
    "answers": {
        "Temperature": u"Die Temperatur im {room} beträgt {state} °C",
        "Humidity": u"Die Luftfeuchtigkeit im {room} beträgt {state} %",
        #"Light": u"Das Licht im {room} ist {state}",
        "Default": u"{equipment} im {room} ist {state}"
    },
    "states": {
        "ON": "an",
        "OFF": "aus",
        "UP": "oben",
        "DOWN": "unten",
        "OPEN": "offen",
        "CLOSED": "geschlossen"
    },
    "main": {
        "replacements": [ [ u"ß", u"ss" ] ], # character cleanups
        "phrase_separator": " und ",
        "phrase_part_matcher": u"(.*[^0-9a-zA-ZäÄöÖüÜ]+|^){}(.*|$)",
        "phrase_full_matcher": u"(.*[^0-9a-zA-ZäÄöÖüÜ]+|^){}([^0-9a-zA-ZäÄöÖüÜ]+.*|$)",
        "phrase_sub": ["vorne","hinten","links","rechts","oben","unten"],
        "phrase_equipment": "eOther_Scenes",
    },
    "commands": {
        "SWITCH": [
            { "value": "OFF", "search": ["aus","ausschalten","beenden","beende","deaktiviere","stoppe","stoppen"], "types": ["Switch","Dimmer","Color"], "tags": ["Power","Light"] },
            { "value": "ON", "search": ["an","ein","einschalten","starten","aktiviere","aktivieren"], "types": ["Switch","Dimmer","Color"], "tags": ["Power","Light"] }
        ],
        "ROLLERSHUTTER": [
            { "value": "DOWN", "search": ["runter","schliessen"], "types": ["Rollershutter"], "tags": ["Control"] },
            { "value": "UP", "search": ["hoch","rauf","öffnen"], "types": ["Rollershutter"], "tags": ["Control"] }
        ],
        "PERCENT": [
            { "value": "REGEX", "search": [u"([0-9a-zA-ZäÄöÖüÜ]+)[\\s]*(prozent|%)"], "types": ["Dimmer","Color"], "tags": ["Light"] }, # default, if search matches
            { "value": "REGEX", "search": [u"([0-9a-zA-ZäÄöÖüÜ]+)[\\s]*(prozent|%)"], "types": ["Dimmer"], "tags": ["ColorTemperature"] }
        ],
        "COLOR": [
            { "value": "REGEX", "search": [u"({})"], "types": ["Color"], "tags": ["Light"] }
        ],
        "COLOR_TEMPERATURE": [
            { "value": "REGEX", "search": [u"({})"], "types": ["Dimmer"], "tags": ["ColorTemperature"] }
        ],
        "READ": [ 
            { "value": "READ", "search": ["wie","wieviel","was","ist","sind"],
                "synonyms": {
                    "warm": "temperatur",
                    "kalt": "temperatur",
                    "feucht": "feuchtigkeit",
                    "trocken": "feuchtigkeit",
                    "luftfeuchtigkeit": "feuchtigkeit",
                }
            } 
        ]
    },
    "mappings": {      
        "COLOR_TEMPERATURE": {
            u"warmweiss": "100",
            u"weiss": "75",
            u"tageslicht": "50",
            u"kaltweiss": "0",
        },
        "COLOR": {}, # will be initialized later
        "PERCENT": {
            u"null": "0",
            u"eins": "1",
            u"zwei": "2",
            u"drei": "3",
            u"vier": "4",
            u"fünf": "5",
            u"sechs": "6",
            u"sieben": "7",
            u"acht": "8",
            u"neun": "9",
            u"zehn": "10",
            u"elf": "11",
            u"zwölf": "12",
            u"dreizehn": "13",
            u"vierzehn": "14",
            u"fünfzehn": "15",
            u"sechzehn": "16",
            u"siebzehn": "17",
            u"achtzehn": "18",
            u"neunzehn": "19",
            u"zwanzig": "20",
            u"einundzwanzig": "21",
            u"zweiundzwanzig": "22",
            u"dreiundzwanzig": "23",
            u"vierundzwanzig": "24",
            u"fünfundzwanzig": "25",
            u"sechsundzwanzig": "26",
            u"siebenundzwanzig": "27",
            u"achtundzwanzig": "28",
            u"neunundzwanzig": "29",
            u"dreissig": "30",
            u"einunddreissig": "31",
            u"zweiunddreissig": "32",
            u"dreiunddreissig": "33",
            u"vierunddreissig": "34",
            u"fünfunddreissig": "35",
            u"sechsunddreissig": "36",
            u"siebenunddreissig": "37",
            u"achtunddreissig": "38",
            u"neununddreissig": "39",
            u"vierzig": "40",
            u"einundvierzig": "41",
            u"zweiundvierzig": "42",
            u"dreiundvierzig": "43",
            u"vierundvierzig": "44",
            u"fünfundvierzig": "45",
            u"sechsundvierzig": "46",
            u"siebenundvierzig": "47",
            u"achtundvierzig": "48",
            u"neunundvierzig": "49",
            u"fünfzig": "50",
            u"einundfünfzig": "51",
            u"zweiundfünfzig": "52",
            u"dreiundfünfzig": "53",
            u"vierundfünfzig": "54",
            u"fünfundfünfzig": "55",
            u"sechsundfünfzig": "56",
            u"siebenundfünfzig": "57",
            u"achtundfünfzig": "58",
            u"neunundfünfzig": "59",
            u"sechzig": "60",
            u"einundsechzig": "61",
            u"zweiundsechzig": "62",
            u"dreiundsechzig": "63",
            u"vierundsechzig": "64",
            u"fünfundsechzig": "65",
            u"sechsundsechzig": "66",
            u"siebenundsechzig": "67",
            u"achtundsechzig": "68",
            u"neunundsechzig": "69",
            u"ziebzig": "70",
            u"einundziebzig": "71",
            u"zweiundziebzig": "72",
            u"dreiundziebzig": "73",
            u"vierundziebzig": "74",
            u"fünfundziebzig": "75",
            u"sechsundziebzig": "76",
            u"siebenundziebzig": "77",
            u"achtundziebzig": "78",
            u"neunundziebzig": "79",
            u"achtzig": "80",
            u"einundachtzig": "81",
            u"zweiundachtzig": "82",
            u"dreiundachtzig": "83",
            u"vierundachtzig": "84",
            u"fünfundachtzig": "85",
            u"sechsundachtzig": "86",
            u"siebenundachtzig": "87",
            u"achtundachtzig": "88",
            u"neuundachtzig": "89",
            u"neunzig": "90",
            u"einundneunzig": "91",
            u"zweiundneunzig": "92",
            u"dreiundneunzig": "93",
            u"vierundneunzig": "94",
            u"fünfundneunzig": "95",
            u"sechsundneunzig": "96",
            u"siebenundneunzig": "97",
            u"achtundneunzig": "98",
            u"neunundneunzig": "99",
            u"hundert": "100"
        }
    }
} 
    
SemanticConfig["mappings"]["COLOR"] = {}
for color_name in ColorConfig["COLOR_NAMES"]:
    color_key = ColorConfig["COLOR_NAMES"][color_name]
    SemanticConfig["mappings"]["COLOR"][color_name] = ColorConfig["COLOR_VALUES"][color_key]

SemanticConfig["commands"]["COLOR"][0]["search"][0] = SemanticConfig["commands"]["COLOR"][0]["search"][0].format("|".join(SemanticConfig["mappings"]["COLOR"].keys()))
SemanticConfig["commands"]["COLOR_TEMPERATURE"][0]["search"][0] = SemanticConfig["commands"]["COLOR_TEMPERATURE"][0]["search"][0].format("|".join(SemanticConfig["mappings"]["COLOR_TEMPERATURE"].keys()))
