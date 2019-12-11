module.exports = {
    "i18n": {
        "nothing_found": "ich habe leider keine Geräte gefunden",
        "nothing_found_in_phrase": "den Teil '{phrase}' habe ich nicht verstanden",
        "no_area_found_in_phrase": "den Ort hab ich in '{phrase}' nicht erkannt",
        "no_cmd_found_in_phrase": "die Aktion habe ich in '{phrase}' nicht erkannt",
        "too_much_found_in_phrase": "für den Teil '{phrase}' habe ich mehr als ein Gerät gefunden",
        "no_devices_found_in_phrase": "für den Teil '{phrase}' habe ich kein Gerät gefunden",
        "ask_to_repeat_everything": "versuche es einfach nochmal",
        "ask_to_repeat_part": "versuche den Teil nochmal",
        "message_join_separator": " und ",
        "message_error_separator": " aber ",
        "ok_message": "ok",
        "help_message": "sage marvin zum beispiel schalte das licht im wohnzimmer an",
        "help_ask_message": "versuche es einfach"
    },
    "main": {
        "__comment": "Types",
        "phrase_separator": " und ",
        "phrase_stop": "stopp",
        "group_other": { "id": "others", "area_prefix": "others_" }
    },
    "clients": [
        {"id":"amzn1.ask.device.{{vault_alexa_device_id1}}","area":"childroom1"},
        {"id":"amzn1.ask.device.{{vault_alexa_device_id2}}","area":"bedroom"},
        {"id":"amzn1.ask.device.{{vault_alexa_device_id3}}","area":null},
        {"id":"amzn1.ask.device.{{vault_alexa_device_id4}}","area":"bathroom"},
        {"id":"amzn1.ask.device.{{vault_alexa_device_id5}}","area":null},
        {"id":"amzn1.ask.device.{{vault_alexa_device_id6}}","area":"floor"},
        {"id":"amzn1.ask.device.{{vault_alexa_device_id7}}","area":"livingroom"}
    ],
    "groups": [
        { "id": "rollershutter", "phrase": ["OR","rolläden","rolladen","rollladen","rollläden"] },
        { "id": "lights", "phrase": ["OR","licht","lampe","beleuchtung"] },
        { "id": "sockets", "phrase": "steckdose" },
        { "id": "temperatures", "phrase": ["OR","temperatur","$warm$"], "i18n": "Im {area} sind es {value} Grad" },
        { "id": "humidity", "phrase": "feuchtigkeit" , "i18n": "Im {area} sind es {value} Grad"},
        { "id": "cameras", "phrase": ["OR", "kamera", "überwachung"] },
        { "id": "electronics" }
    ],
    "commands": [
        {
            "__comment": "Commands for lights, sockets, electronics and others",
            "groups": ["lights","sockets","electronics","others"],
            "commands": [
                { "id": "ACTION_OFF", "phrase": ["OR","$aus$","$ausschalten$","$beenden$","$beende$","$deaktiviere$","$stoppe$","$stoppen$"] },
                { "id": "ACTION_ON", "phrase": ["OR","$an$","$ein$","$einschalten$","$starten$","$aktiviere$","$aktivieren$"] }
            ]
        },{
            "__comment": "Commands for lights",
            "groups": ["lights"],
            "commands": [
                { "id": "ACTION_PERCENT", "phrase": "/.* ([0-9a-zA-ZäÄöÖüÜ]+)[\\s]*(prozent|%).*/" }
            ]
        },{
            "__comment": "Commands for shutters",
            "groups": ["rollershutter"],
            "commands": [
                { "id": "ACTION_DOWN", "phrase": ["OR","$runter$","$schliessen$"] },
                { "id": "ACTION_UP", "phrase": ["OR","$hoch$","$öffnen$"] }
            ]
        },{
            "__comment": "Commands for sensors",
            "groups": ["temperatures","humidity","cameras"],
            "commands": [
                { "id": "READ_VALUE" }
            ]
        },{
            "__comment": "Commands for electronics and others",
            "groups": ["electronics","others"],
            "commands": [
                { "id": "DEFAULT_ON" }
            ]
        }
    ],
    "areas": [
        {
            "__comment": "Main areas for all groups",
            "groups": ["all"],
            "details": [
                {
                    "parent_area_id": null,
                    "sub_areas": [
                        {"id": "others_automower", "phrase": ["OR", "mower", "rasen"]},
                        {"id": "others_good_morning", "phrase": ["OR", "guten morgen", "aufstehen"]},
                        {"id": "others_go_sleeping", "phrase": ["AND", "$schlafen", "geh"]},
                        {"id": "others_good_night", "phrase": "gute nacht"},
                        {"id": "others_going_out", "phrase": ["AND", [ "OR", "$raus$", "$draußen$"],["OR", "$bin", "$geh"]]},
                        {"id": "others_coming_back", "phrase": ["AND", ["OR","$bin$","$wieder$"], ["OR", "$da$", "$zurück$"]]},

                        {"id": "livingroom", "phrase": ["OR", "$wohnzimmer", "$wohn$"]}, // im wohn und schlafzimmer
                        {"id": "boxroom", "phrase": ["OR", "$abstellkammer", "$kammer"]},
                        {"id": "utilityroom", "phrase": "$hwr"},
                        {"id": "guestwc", "phrase": ["AND", "$gäste", ["OR", "bad", "wc", "toilette"]]},
                        {"id": "guestroom", "phrase": ["OR", "$gästezimmer", ["AND", "$gäste$", "!<guestwc>"], "$bastelzimmer"]},
                        {"id": "kitchen", "phrase": "$küche"},
                        {"id": "floor", "phrase": "$flur"},

                        {"id": "bathroom", "phrase": ["AND", "bad", "!<guestwc>"]},

                        {"id": "bedroom", "phrase": ["OR", "$schlafzimmer", "$schlaf$"]}, // im schlaf und wohnzimmer
                        {"id": "dressingroom", "phrase": "$ankleide"},
                        {"id": "childroom", "phrase": "$kind"},
                        {"id": "attic", "phrase": "$dachboden"},
                        {"id": "terrace", "phrase": "$terasse"},
                        {"id": "frontdoor", "phrase": ["OR", "$haustür", "$eingangstür"]},
                        {"id": "carport", "phrase": ["AND",["OR", "$auto", "$carport"],"!<others_automower>"]},

                        {"id": "garage_streedside", "phrase": ["AND", "$schuppen", ["OR", "vorne", "strasse"]]},
                        {"id": "garage_gardenside", "phrase": ["AND", "$schuppen", "!<garage_streedside>"]},

                        {"id": "upstairs", "phrase": ["AND", "$obergeschoss", "!<floor>"]},
                        {"id": "downstairs", "phrase": ["AND", ["OR", "$untergeschoss", "$erdgeschoss"], "!<floor>"]},

                        {"id": "indoor", "phrase": ["OR", "innen", "im haus"]},
                        {"id": "outdoor_streedside","phrase": ["AND", ["OR", "aussen", "garten"], ["OR", "vorne", "strasse"]]},
                        {"id": "outdoor_gardenside", "phrase": ["AND", ["OR", "aussen", "garten"], "hinten"]}
                    ]
                }
            ]
        },{
            "__comment": "Main areas fallbacks. Is used if no main area was detected before.",
            "groups": ["all"],
            "details": [
                {
                    "parent_area_id": "fallback",
                    "sub_areas": [
                        {"id": "upstairs", "phrase": ["AND", ["OR", "$oben", "$obergeschoss"], "!<floor>"]},
                        {"id": "downstairs","phrase": ["AND", ["OR", "$unten", "$untergeschoss", "$erdgeschoss"], "!<floor>"]},
                        {"id": "outdoor", "phrase": ["OR", "$aussen", "$garten"]},
                        {"id": "all", "phrase": ["OR", "$alle$", "$komplett$", "$vollständig$", "$überall$"]}
                    ]
                }
            ]
        },{
            "__comment": "Sub areas.",
            "groups": ["rollershutter","lights","sockets","temperatures","humidity"],
            "details": [
                {
                    "parent_area_id": "floor",
                    "sub_areas": [
                        { "id": "floor_sf", "phrase": ["OR","$oben$","$obergeschoss$"] },
                        { "id": "floor_ff", "phrase": ["OR","$unten$","$untergeschoss$","$erdgeschoss$"] }
                    ]
                }
            ]
        },{
            "__comment": "Sub areas for groups.",
            "groups": ["lights"],
            "details": [
                {
                    "parent_area_id": "livingroom",
                    "sub_areas": [
                        { "id": "livingroom_bar", "phrase": "$tresen" },

                        { "id": "livingroom_standard_lamp_up", "phrase": ["AND","stehlampe","$oben$"] },
                        { "id": "livingroom_standard_lamp_down", "phrase": ["AND","stehlampe","$unten$"] },
                        { "id": "livingroom_standard_lamp", "phrase": ["AND","stehlampe","!<livingroom_standard_lamp_up>","!<livingroom_standard_lamp_down>"] },

                        { "id": "livingroom_bassbox_indirect", "phrase": "bassbox" },
                        { "id": "livingroom_couch_indirect", "phrase": ["AND","couch",["OR","$indirekt","$hinte","$versteckt"]] },
                        { "id": "livingroom_couch_decke", "phrase": ["AND","couch","!<livingroom_couch_indirect>"] },

                        { "id": "livingroom_dining_table_ceiling", "phrase": "esstisch" },

                        { "id": "livingroom_indirect_all", "phrase": ["AND","indirekt","!<livingroom_couch_indirect>","!<livingroom_bar>"] },
                        { "id": "livingroom_ceiling_all", "phrase": ["AND","decke","!<livingroom_dining_table_ceiling>","decke","!<livingroom_couch_decke>"] }
                    ]
                },{
                    "parent_area_id": "kitchen",
                    "sub_areas": [
                        { "id": "kitchen_cupboard", "phrase": "schrank" },
                        { "id": "kitchen_ceiling", "phrase": "decke" }
                    ]
                },{
                    "parent_area_id": "floor",
                    "sub_areas": [
                        { "id": "floor_ff_mirror", "phrase": "spiegel" },
                        { "id": "floor_ff_indirekt", "phrase": "$indirekt" },
                        { "id": "floor_ff_ceil", "phrase": "decke" }
                    ]
                },{
                    "parent_area_id": "guestwc",
                    "sub_areas": [
                        { "id": "guestwc_mirror", "phrase": "spiegel" },
                        { "id": "guestwc_ceiling", "phrase": "decke" }
                    ]
                },{
                    "parent_area_id": "bathroom",
                    "sub_areas": [
                        { "id": "bathroom_mirror", "phrase": "spiegel" },
                        { "id": "bathroom_ceiling", "phrase": "decke" }
                    ]
                },{
                    "parent_area_id": "childroom",
                    "sub_areas": [
                        { "id": "childroom1", "phrase": ["OR","1", "eins","vorne"]},
                        { "id": "childroom2", "phrase": ["OR","2", "zwei","hinten"]}
                    ]
                },{
                    "parent_area_id": "bedroom",
                    "sub_areas": [
                        { "id": "bedroom_ceiling", "phrase": "decke" },
                        { "id": "bedroom_left", "phrase": ["OR","fenster","links"] },
                        { "id": "bedroom_right", "phrase": ["OR","wand","rechts"] }
                    ]
                },{
                    "parent_area_id": "all",
                    "sub_areas": [
                        { "id": "all_indirect", "phrase": "$indirekt" }
                    ]
                }
            ]
        },{
            "__comment": "Sub areas.",
            "groups": ["electronics"],
            "details": [
                {
                    "parent_area_id": "livingroom",
                    "sub_areas": [
                        { "id": "livingroom_tv", "phrase": "fernseh" },
                        { "id": "livingroom_ps4", "phrase": "ps4"},
                        { "id": "livingroom_receiver", "phrase": "stereo"},
                        { "id": "livingroom_bassbox", "phrase": "bassbox"}
                    ]
                }
            ]
        },{
            "__comment": "Sub areas.",
            "groups": ["electronics"],
            "details": [
                {
                    "parent_area_id": "livingroom_tv",
                    "sub_areas": [
                        { "id": "livingroom_tv_volumeup", "phrase": "lauter" },
                        { "id": "livingroom_tv_volumedown", "phrase": "leiser" },
                        { "id": "livingroom_tv_mute", "phrase": ["AND",["OR","lautlos","still","ton","laut"],"!<livingroom_tv_volumeup>","!<livingroom_tv_volumedown>"] },
                        { "id": "livingroom_tv_input_hdmi1", "phrase": ["OR","sat",["AND",["OR","input","hdmi"],"eins"]] },
                        { "id": "livingroom_tv_input_hdmi2", "phrase": ["OR","playstation","p. s. vier",["AND",["OR","input","hdmi"],"zwei"]] },
                        { "id": "livingroom_tv_input_hdmi3", "phrase": ["OR","chromecast",["AND",["OR","input","hdmi"],"drei"]] },
                        { "id": "livingroom_tv_input_hdmi4", "phrase": ["AND",["OR","input","hdmi"],"vier","!<livingroom_tv_input_hdmi2>"] },
                        { "id": "livingroom_tv_channel_ard", "phrase": ["OR", "ARD", ["AND","kanal","eins"] ] },
                        { "id": "livingroom_tv_channel_zdf", "phrase": ["OR", "ZDF", ["AND","kanal","zwei"] ] },
                        { "id": "livingroom_tv_channel_rtl", "phrase": ["OR", "RTL", ["AND","kanal","drei"] ] },
                        { "id": "livingroom_tv_channel_sat1", "phrase": ["OR", "SAT1", ["AND","kanal","vier"] ] },
                        { "id": "livingroom_tv_channel_pro7", "phrase": ["OR", "PRO7", ["AND","kanal","fünf"] ] },
                        { "id": "livingroom_tv_channel_servustv", "phrase": ["OR", "Servus TV", ["AND","kanal","sechs"] ] },
                        { "id": "livingroom_tv_channel_vox", "phrase": ["OR", "VOX", ["AND","kanal","sieben"] ] },
                        { "id": "livingroom_tv_channel_kabel1", "phrase": ["OR", "Kabel1", ["AND","kanal","acht"] ] },
                        { "id": "livingroom_tv_channel_dmax", "phrase": ["OR", "DMAX", ["AND","kanal","neun"] ] },
                        { "id": "livingroom_tv_channel_tlc", "phrase": ["OR", "TLC", ["AND","kanal","zehn"] ] },
                        { "id": "livingroom_tv_channel_n24", "phrase": ["OR", "N24", ["AND","kanal","elf"] ] },
                        { "id": "livingroom_tv_channel_ntv", "phrase": ["OR", "NTV", ["AND","kanal","zwölf"] ] },
                        { "id": "livingroom_tv_channel_tagesschau24", "phrase": ["OR", "Tagesschau 24", ["AND","kanal","dreizehn"] ] },
                        { "id": "livingroom_tv_channel_pro7max", "phrase": ["OR", "Pro7 Max", ["AND","kanal","vierzehn"] ] },
                        { "id": "livingroom_tv_channel_sat1gold", "phrase": ["OR", "Sat1 Gold", ["AND","kanal","fünfzehn"] ] },
                        { "id": "livingroom_tv_channel_sixx", "phrase": ["OR", "SIXX", ["AND","kanal","sechzehn"] ] },
                        { "id": "livingroom_tv_channel_rtl2", "phrase": ["OR", "RTL2", ["AND","kanal","siebzehn"] ] },
                        { "id": "livingroom_tv_channel_nitro", "phrase": ["OR", "Nitro", ["AND","kanal","achtzehn"] ] },
                        { "id": "livingroom_tv_channel_superrtl", "phrase": ["OR", "Super RTL", ["AND","kanal","neunzehn"] ] },
                        { "id": "livingroom_tv_channel_tele5", "phrase": ["OR", "Tele 5", ["AND","kanal","zwanzig"] ] },
                        { "id": "livingroom_tv_channel_weltderwunder", "phrase": ["OR", "Tele 5", ["AND","kanal","einundzwanzig"] ] },
                        { "id": "livingroom_tv_channel_arte", "phrase": ["OR", "Arte", ["AND","kanal","zweiundzwanzig"] ] },
                        { "id": "livingroom_tv_channel_zdfinfo", "phrase": ["OR", "ZDF Info", ["AND","kanal","dreiundzwanzig"] ] },
                        { "id": "livingroom_tv_channel_phoenix", "phrase": ["OR", "Phoenix", ["AND","kanal","vierundzwanzig"] ] },
                        { "id": "livingroom_tv_channel_one", "phrase": ["OR", "One", ["AND","kanal","fünfundzwanzig"] ] },
                        { "id": "livingroom_tv_channel_zdfneo", "phrase": ["OR", "ZDF Neo", ["AND","kanal","sechsundzwanzig"] ] },
                        { "id": "livingroom_tv_channel_3sat", "phrase": ["OR", "3Sat", ["AND","kanal","siebenundzwanzig"] ] }
                    ]
                }
            ]
        }
    ],
    "actions": {
        "rollershutter": [
            { "id": "Shutters_FF_Livingroom_Couch", "areas": ["livingroom_couch"], "items": ["Shutters_FF_Livingroom_Couch"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_FF_Livingroom_Terrace", "areas": ["livingroom_terrace"], "items": ["Shutters_FF_Livingroom_Terrace"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_FF_Livingroom", "areas": ["livingroom"], "items": ["Shutters_FF_Livingroom_Couch","Shutters_FF_Livingroom_Terrace"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_FF_Kitchen", "areas": ["kitchen"], "items": ["Shutters_FF_Kitchen"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_FF_Guestroom", "areas": ["guestroom"], "items": ["Shutters_FF_Guestroom"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_FF_GuestWC", "areas": ["guestwc"], "items": ["Shutters_FF_GuestWC"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF_Bedroom", "areas": ["bedroom"], "items": ["Shutters_SF_Bedroom"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF_Dressingroom", "areas": ["dressingroom"], "items": ["Shutters_SF_Dressingroom"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF_Child1", "areas": ["childroom1"], "items": ["Shutters_SF_Child1"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF_Child2", "areas": ["childroom2"], "items": ["Shutters_SF_Child2"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF_Bathroom", "areas": ["bathroom"], "items": ["Shutters_SF_Bathroom"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF_Attic", "areas": ["attic"], "items": ["Shutters_SF_Attic"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_SF", "areas": ["upstairs"], "items": ["Shutters_SF"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters_FF", "areas": ["downstairs"], "items": ["Shutters_FF"], "cmds": ["ACTION_UP","ACTION_DOWN"] },
            { "id": "Shutters", "areas": ["indoor","all"], "items": ["Shutters"], "cmds": ["ACTION_UP","ACTION_DOWN"] }
        ],
        "lights": [
            { "id": "Light_FF_Floor_Mirror", "areas": ["floor_ff_mirror"], "items": ["Light_FF_Floor_Mirror"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_FF_Floor_Hue_Brightness", "areas": ["floor_ff_indirekt"], "items": ["Light_FF_Floor_Hue_Brightness"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Floor_Ceiling", "areas": ["floor_ff_ceil"], "items": ["Light_FF_Floor_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_Floor_On", "areas": ["floor","floor_ff"], "items": ["Light_FF_Floor_Ceiling"], "cmds": ["ACTION_ON"] },
            { "id": "Light_Floor_Off", "areas": ["floor","floor_ff"], "items": ["Light_FF_Floor_Ceiling","Light_FF_Floor_Hue_Brightness","Light_FF_Floor_Mirror","Light_SF_Floor_Ceiling"], "cmds": ["ACTION_OFF"] },

            { "id": "Light_FF_GuestWC_Mirror", "areas": ["guestwc_mirror"], "items": ["Light_FF_GuestWC_Mirror"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_FF_GuestWC_Ceiling", "areas": ["guestwc_ceiling"], "items": ["Light_FF_GuestWC_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_FF_GuestWC_On", "areas": ["guestwc"], "items": ["Light_FF_GuestWC_Ceiling"], "cmds": ["ACTION_ON"] },
            { "id": "Light_FF_GuestWC_Off", "areas": ["guestwc"], "items": ["Light_FF_GuestWC_Ceiling","Light_FF_GuestWC_Mirror"], "cmds": ["ACTION_OFF"] },

            { "id": "Light_FF_Utilityroom_Ceiling", "areas": ["utilityroom"], "items": ["Light_FF_Utilityroom_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_FF_Boxroom_Ceiling", "areas": ["boxroom"], "items": ["Light_FF_Boxroom_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_FF_Kitchen_Cupboard", "areas": ["kitchen_cupboard"], "items": ["Light_FF_Kitchen_Cupboard"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_FF_Kitchen_Dimmable", "areas": ["kitchen_ceiling"], "items": ["Light_FF_Kitchen_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Kitchen_Ceiling", "areas": ["kitchen"], "items": ["Light_FF_Kitchen_Ceiling"], "cmds": ["ACTION_ON","ACTION_PERCENT"] },
            { "id": "Light_FF_Kitchen_Switch", "areas": ["kitchen"], "items": ["Light_FF_Kitchen_Ceiling","Light_FF_Kitchen_Cupboard"], "cmds": ["ACTION_OFF"] },

            { "id": "Light_FF_Livingroom_Hue_Brightness4", "areas": ["livingroom_bar"], "items": ["Light_FF_Livingroom_Hue_Brightness4"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Hue_Brightness3", "areas": ["livingroom_standard_lamp_up"], "items": ["Light_FF_Livingroom_Hue_Brightness3"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Hue_Brightness2", "areas": ["livingroom_standard_lamp_down"], "items": ["Light_FF_Livingroom_Hue_Brightness2"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Hue_Brightness3_2", "areas": ["livingroom_standard_lamp"], "items": ["Light_FF_Livingroom_Hue_Brightness3","Light_FF_Livingroom_Hue_Brightness2"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Hue_Brightness1", "areas": ["livingroom_couch_indirect","livingroom_bassbox_indirect"], "items": ["Light_FF_Livingroom_Hue_Brightness1"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Couch", "areas": ["livingroom_couch_decke"], "items": ["Light_FF_Livingroom_Couch"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Diningtable", "areas": ["livingroom_dining_table_ceiling"], "items": ["Light_FF_Livingroom_Diningtable"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Ceil", "areas": ["livingroom_ceiling_all"], "items": ["Light_FF_Livingroom_Couch","Light_FF_Livingroom_Diningtable"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Hue_Brightness", "areas": ["livingroom_indirect_all"], "items": ["Light_FF_Livingroom_Hue_Brightness"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_On", "areas": ["livingroom"], "items": ["Light_FF_Livingroom_Couch","Light_FF_Livingroom_Diningtable"], "cmds": ["ACTION_ON","ACTION_PERCENT"] },
            { "id": "Light_FF_Livingroom_Off", "areas": ["livingroom"], "items": ["Light_FF_Livingroom_Couch","Light_FF_Livingroom_Diningtable","Light_FF_Livingroom_Hue_Brightness"], "cmds": ["ACTION_OFF"] },

            { "id": "Light_FF_Guestroom_Ceiling", "areas": ["guestroom"], "items": ["Light_FF_Guestroom_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_SF_Floor_Ceiling", "areas": ["floor_sf"], "items": ["Light_SF_Floor_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_SF_Child1_Ceiling", "areas": ["childroom1"], "items": ["Light_SF_Child1_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_SF_Child2_Ceiling", "areas": ["childroom2"], "items": ["Light_SF_Child2_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_SF_Bedroom_Ceiling", "areas": ["bedroom_ceiling"], "items": ["Light_SF_Bedroom_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_SF_Bedroom_Left", "areas": ["bedroom_left"], "items": ["Light_SF_Bedroom_Left_Hue_Brightness"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_SF_Bedroom_Right", "areas": ["bedroom_right"], "items": ["Light_SF_Bedroom_Right_Hue_Brightness"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_SF_Bedroom_On", "areas": ["bedroom"], "items": ["Light_SF_Bedroom_Ceiling"], "cmds": ["ACTION_ON"] },
            { "id": "Light_SF_Bedroom_Off", "areas": ["bedroom"], "items": ["Light_SF_Bedroom_Ceiling","Light_SF_Bedroom_Left_Hue_Brightness","Light_SF_Bedroom_Right_Hue_Brightness"], "cmds": ["ACTION_OFF"] },

            { "id": "Light_SF_Dressingroom_Ceiling", "areas": ["dressingroom"], "items": ["Light_SF_Dressingroom_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_SF_Bathroom_Mirror", "areas": ["bathroom_mirror"], "items": ["Light_SF_Bathroom_Mirror"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_SF_Bathroom_Ceiling", "areas": ["bathroom_ceiling"], "items": ["Light_SF_Bathroom_Ceiling"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_SF_Bathroom_On", "areas": ["bathroom"], "items": ["Light_SF_Bathroom_Ceiling"], "cmds": ["ACTION_ON"] },
            { "id": "Light_SF_Bathroom_Off", "areas": ["bathroom"], "items": ["Light_SF_Bathroom_Ceiling","Light_SF_Bathroom_Mirror"], "cmds": ["ACTION_OFF"] },

            { "id": "Light_SF_Attic", "areas": ["attic"], "items": ["Light_SF_Attic"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_FirstFloor_Dimmable", "areas": ["downstairs","indoor","all"], "items": ["Light_FF_Floor_Hue_Brightness","Light_FF_Kitchen_Ceiling","Light_FF_Livingroom_Hue_Brightness","Light_FF_Livingroom_Couch","Light_FF_Livingroom_Diningtable"], "cmds": ["ACTION_PERCENT"] },
            { "id": "Light_FirstFloor_Switchable", "areas": ["downstairs"], "items": ["Lights_FF"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_SecondFloor_Switchable", "areas": ["upstairs"], "items": ["Lights_SF"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_Indoor_Switchable", "areas": ["indoor","all"], "items": ["Lights_Indoor"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_All_Indirect", "areas": ["all_indirect"], "items": ["Light_FF_Floor_Hue_Brightness","Light_FF_Livingroom_Hue_Brightness"], "cmds": ["ACTION_PERCENT"] },

            { "id": "Light_Outdoor_Garage_Streedside_Manual", "areas": ["garage_streedside"], "items": ["Light_Outdoor_Garage_Streedside_Manual"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_Outdoor_Frontdoor_Manual", "areas": ["frontdoor"], "items": ["Light_Outdoor_Frontdoor_Manual"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_Outdoor_Carport_Manual", "areas": ["carport"], "items": ["Light_Outdoor_Carport_Manual"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Light_Outdoor_Terrace_Manual", "areas": ["terrace"], "items": ["Light_Outdoor_Terrace_Manual"], "cmds": ["ACTION_ON","ACTION_OFF","ACTION_PERCENT"] },
            { "id": "Light_Outdoor_Garage_Gardenside_Manual", "areas": ["garage_gardenside"], "items": ["Light_Outdoor_Garage_Gardenside_Manual"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Light_Outdoor_Dimmable", "areas": ["outdoor"], "items": ["Light_Outdoor_Terrace_Manual"], "cmds": ["ACTION_PERCENT"] },
            { "id": "Light_Outdoor_Switchable", "areas": ["outdoor"], "items": ["Lights_Outdoor"], "cmds": ["ACTION_ON","ACTION_OFF"] }
        ],
        "sockets": [
            { "id": "Socket_Livingroom", "areas": ["livingroom"], "items": ["Socket_Livingroom"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Socket_Floor", "areas": ["floor"], "items": ["Socket_Floor"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Socket_GuestWC", "areas": ["guestwc"], "items": ["Socket_GuestWC"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Socket_Attic", "areas": ["attic"], "items": ["Socket_Attic"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Sockets_Outdoor", "areas": ["outdoor"], "items": ["Sockets_Outdoor"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Socket_Streedside", "areas": ["outdoor_streedside"], "items": ["Socket_Streedside"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Socket_Gardenside", "areas": ["outdoor_gardenside"], "items": ["Socket_Gardenside"], "cmds": ["ACTION_ON","ACTION_OFF"] }
        ],
        "temperatures": [
            { "id": "Temperature_FF_Livingroom",  "areas": ["livingroom"], "items": ["Temperature_FF_Livingroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_FF_Boxroom",  "areas": ["boxroom"], "items": ["Temperature_FF_Boxroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_FF_Guestroom",  "areas": ["guestroom"], "items": ["Temperature_FF_Guestroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_FF_GuestWC",  "areas": ["guestwc"], "items": ["Temperature_FF_GuestWC"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_FF_Floor",  "areas": ["floor","floor_ff"], "items": ["Temperature_FF_Floor"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_FF_Utilityroom",  "areas": ["utilityroom"], "items": ["Temperature_FF_Utilityroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_FF_Garage",  "areas": ["carport"], "items": ["Temperature_FF_Garage"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Bedroom",  "areas": ["bedroom"], "items": ["Temperature_SF_Bedroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Dressingroom",  "areas": ["dressingroom"], "items": ["Temperature_SF_Dressingroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Child1",  "areas": ["childroom1"], "items": ["Temperature_SF_Child1"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Child2",  "areas": ["childroom2"], "items": ["Temperature_SF_Child2"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Bathroom",  "areas": ["bathroom"], "items": ["Temperature_SF_Bathroom"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Floor",  "areas": ["floor_sf"], "items": ["Temperature_SF_Floor"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_SF_Attic",  "areas": ["attic"], "items": ["Temperature_SF_Attic"], "cmds": ["READ_VALUE"] },
            { "id": "Temperature_Garden",  "areas": ["outdoor"], "items": ["Temperature_Garden"], "cmds": ["READ_VALUE"] }
        ],
        "humidity": [
            { "id": "Humidity_FF_Livingroom", "areas": ["livingroom"], "items": ["Humidity_FF_Livingroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_FF_Boxroom", "areas": ["boxroom"], "items": ["Humidity_FF_Boxroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_FF_Guestroom", "areas": ["guestroom"], "items": ["Humidity_FF_Guestroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_FF_GuestWC", "areas": ["guestwc"], "items": ["Humidity_FF_GuestWC"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_FF_Floor", "areas": ["floor","floor_ff"], "items": ["Humidity_FF_Floor"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_FF_Utilityroom", "areas": ["utilityroom"], "items": ["Humidity_FF_Utilityroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_FF_Garage", "areas": ["carport"], "items": ["Humidity_FF_Garage"], "cmds": ["READ_VALUE"] },

            { "id": "Humidity_SF_Bedroom", "areas": ["bedroom"], "items": ["Humidity_SF_Bedroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_SF_Dressingroom", "areas": ["dressingroom"], "items": ["Humidity_SF_Dressingroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_SF_Child1", "areas": ["childroom1"], "items": ["Temperature_SF_Child1"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_SF_Child2", "areas": ["childroom1"], "items": ["Humidity_SF_Child2"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_SF_Bathroom", "areas": ["bathroom"], "items": ["Humidity_SF_Bathroom"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_SF_Floor", "areas": ["floor_sf"], "items": ["Humidity_SF_Floor"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_SF_Attic", "areas": ["attic"], "items": ["Humidity_SF_Attic"], "cmds": ["READ_VALUE"] },
            { "id": "Humidity_Garden", "areas": ["outdoor"], "items": ["Humidity_Garden"], "cmds": ["READ_VALUE"] }
        ],
        "electronics": [
            { "id": "Socket_Bassbox", "areas": ["livingroom_bassbox"], "items": ["Socket_Bassbox"], "cmds": ["ACTION_ON","ACTION_OFF"] },

            { "id": "Controll_Tv_power", "areas": ["livingroom_tv"], "items": ["Scene6"], "cmds": ["ACTION_ON","ACTION_OFF"] },
            { "id": "Controll_Tv_volumeup", "areas": ["livingroom_tv_volumeup"], "items": ["TV_KEY_VOLUMEUP"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_volumedown", "areas": ["livingroom_tv_volumedown"], "items": ["TV_KEY_VOLUMEDOWN"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_mute", "areas": ["livingroom_tv_mute"], "items": ["TV_KEY_MUTE"], "cmds": ["DEFAULT_ON","ACTION_ON","ACTION_OFF"] },
            { "id": "Controll_Tv_input_hdmi1", "areas": ["livingroom_tv_input_hdmi1"], "items": ["TV_KEY_1"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_input_hdmi2", "areas": ["livingroom_tv_input_hdmi2"], "items": ["TV_KEY_2"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_input_hdmi3", "areas": ["livingroom_tv_input_hdmi3"], "items": ["TV_KEY_3"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_input_hdmi4", "areas": ["livingroom_tv_input_hdmi4"], "items": ["TV_KEY_4"], "cmds": ["DEFAULT_ON","ACTION_ON"] },

            { "id": "Controll_Tv_Channel_ARD", "areas": ["livingroom_tv_channel_ard"], "items": ["SAT_KEY_ARD"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_ZDF", "areas": ["livingroom_tv_channel_zdf"], "items": ["SAT_KEY_ZDF"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_RTL", "areas": ["livingroom_tv_channel_rtl"], "items": ["SAT_KEY_RTL"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_SAT1", "areas": ["livingroom_tv_channel_sat1"], "items": ["SAT_KEY_SAT1"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_PRO7", "areas": ["livingroom_tv_channel_pro7"], "items": ["SAT_KEY_PRO7"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_SERVUSTV", "areas": ["livingroom_tv_channel_servustv"], "items": ["SAT_KEY_SERVUSTV"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_VOX", "areas": ["livingroom_tv_channel_vox"], "items": ["SAT_KEY_VOX"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_KABEL1", "areas": ["livingroom_tv_channel_kabel1"], "items": ["SAT_KEY_KABEL1"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_DMAX", "areas": ["livingroom_tv_channel_dmax"], "items": ["SAT_KEY_DMAX"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_TLC", "areas": ["livingroom_tv_channel_tlc"], "items": ["SAT_KEY_TLC"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_N24", "areas": ["livingroom_tv_channel_n24"], "items": ["SAT_KEY_N24"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_NTV", "areas": ["livingroom_tv_channel_ntv"], "items": ["SAT_KEY_NTV"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_TAGESSCHAU24", "areas": ["livingroom_tv_channel_tagesschau24"], "items": ["SAT_KEY_TAGESSCHAU24"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_PRO7MAX", "areas": ["livingroom_tv_channel_pro7max"], "items": ["SAT_KEY_PRO7MAX"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_SAT1GOLD", "areas": ["livingroom_tv_channel_sat1gold"], "items": ["SAT_KEY_SAT1GOLD"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_SIXX", "areas": ["livingroom_tv_channel_sixx"], "items": ["SAT_KEY_SIXX"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_RTL2", "areas": ["livingroom_tv_channel_rtl2"], "items": ["SAT_KEY_RTL2"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_NITRO", "areas": ["livingroom_tv_channel_nitro"], "items": ["SAT_KEY_NITRO"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_SUPERRTL", "areas": ["livingroom_tv_channel_superrtl"], "items": ["SAT_KEY_SUPERRTL"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_TELE5", "areas": ["livingroom_tv_channel_tele5"], "items": ["SAT_KEY_TELE5"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_WELTDERWUNDER", "areas": ["livingroom_tv_channel_weltderwunder"], "items": ["SAT_KEY_WELTDERWUNDER"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_ARTE", "areas": ["livingroom_tv_channel_arte"], "items": ["SAT_KEY_ARTE"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_ZDFINFO", "areas": ["livingroom_tv_channel_zdfinfo"], "items": ["SAT_KEY_ZDFINFO"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_PHOENIX", "areas": ["livingroom_tv_channel_phoenix"], "items": ["SAT_KEY_PHOENIX"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_ONE", "areas": ["livingroom_tv_channel_one"], "items": ["SAT_KEY_ONE"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_ZDFNEO", "areas": ["livingroom_tv_channel_zdfneo"], "items": ["SAT_KEY_ZDFNEO"], "cmds": ["DEFAULT_ON","ACTION_ON"] },
            { "id": "Controll_Tv_Channel_3SAT", "areas": ["livingroom_tv_channel_3sat"], "items": ["SAT_KEY_3SAT"], "cmds": ["DEFAULT_ON","ACTION_ON"] }
        ],
        "others": [

            { "id": "Automower", "areas": ["others_automower"], "items": [], "cmds": ["DEFAULT_ON"] },

            { "id": "Scene2", "areas": ["others_good_morning"], "items": ["Scene2"], "cmds": ["DEFAULT_ON"], "i18n": "guten morgen" },
            { "id": "Scene3", "areas": ["others_go_sleeping"], "items": ["Scene3"], "cmds": ["DEFAULT_ON"] },
            { "id": "Scene4", "areas": ["others_good_night"], "items": ["Scene4"], "cmds": ["DEFAULT_ON"], "i18n": "gute nacht" },
            { "id": "Scene5", "areas": ["others_going_out"], "items": ["Scene5"], "cmds": ["DEFAULT_ON"], "i18n": "ok. Ich habe die automatische Beleuchtung dafür teilweise ausgeschaltet" },
            { "id": "Scene5", "areas": ["others_coming_back"], "items": ["Motiondetector_Outdoor_Switch"], "cmds": ["DEFAULT_ON"], "i18n": "ok. Ich habe die automatische Beleuchtung wieder komplett eingeschaltet" },
        ]
    }
}
