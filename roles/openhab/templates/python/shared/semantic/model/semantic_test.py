# -*- coding: utf-8 -*-
Cases = {
    "enabled_bak": [
        { "phrase": u"alle rollläden hoch und fernseher an", "client_id": "amzn1.ask.device.AFUSC2ZJY7NS7773FR5SXTQXXG6RX7B5RFFABEINCTSUNSNWBXUVICA3JDXEZSNBEXEXFRFYSRT3KSGQRRQQSK5YXLH4VWRWF6KEWSEP7RCLPXTYIPFZ7VHFYT36JOALTJJTNYGRYID6E2EYWGOEPGEPYN7Q", "items": [[ "Scene6", "ACTION_ON" ]] },
        { "phrase": u"licht im wohnzimmer und aussen licht und steckdosen aus", "items": [[ "Light_FF_Livingroom_Couch", "ACTION_OFF" ],[ "Light_FF_Livingroom_Diningtable", "ACTION_OFF" ], [ "Light_FF_Livingroom_Hue_Color", "ACTION_OFF" ],[ "Lights_Outdoor", "ACTION_OFF" ],[ "Sockets_Outdoor", "ACTION_OFF" ]] },
        { "phrase": u"Hallo", "items": [[ "Scene6", "ACTION_ON" ]] },
        { "phrase": u"wohnzimmer fernseher an", "items": [[ "Scene6", "ACTION_ON" ]] },
        { "phrase": u"licht wohnzimmer automower und licht flur schlafzimmer und schuppen an", "items": [[None],[None],[ "Light_FF_Livingroom_Couch", "ACTION_ON" ],[ "Light_FF_Livingroom_Diningtable", "ACTION_ON" ],[ "Light_FF_Floor_Ceiling", "ACTION_ON" ],[ "Light_SF_Bedroom_Ceiling", "ACTION_ON" ],[ "Light_Outdoor_Garage_Gardenside_Manual", "ACTION_ON" ]] }
    ],
    "enabled1": [
        { "phrase": u"licht innen aus und rollläden obergeschoss runter", "items": [["pGF_Guesttoilet_Light_Ceiling_Powered","OFF"],["pGF_Guesttoilet_Light_Mirror_Powered","OFF"],["pGF_Utilityroom_Light_Ceiling_Powered","OFF"],["pGF_Boxroom_Light_Ceiling_Powered","OFF"],["pGF_Kitchen_Light_Ceiling_Brightness","OFF"],["pGF_Kitchen_Light_Cupboard_Powered","OFF"],["pGF_Livingroom_Light_Diningtable_Brightness","OFF"],["pGF_Livingroom_Light_Hue4_Color","OFF"],["pGF_Livingroom_Light_Hue5_Color","OFF"],["pGF_Livingroom_Light_Hue1_Color","OFF"],["pGF_Livingroom_Light_Hue2_Color","OFF"],["pGF_Livingroom_Light_Hue3_Color","OFF"],["pGF_Livingroom_Light_Couchtable_Brightness","OFF"],["pGF_Guestroom_Light_Ceiling_Powered","OFF"],["pGF_Corridor_Light_Hue_Color","OFF"],["pGF_Corridor_Light_Mirror_Powered","OFF"],["pGF_Corridor_Light_Ceiling_Powered","OFF"],["pGF_Garage_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Light_Mirror_Powered","OFF"],["pFF_Dressingroom_Light_Ceiling_Powered","OFF"],["pFF_Bedroom_Light_Hue_Right_Color","OFF"],["pFF_Bedroom_Light_Hue_Left_Color","OFF"],["pFF_Bedroom_Light_Ceiling_Powered","OFF"],["pFF_Child1_Light_Ceiling_Powered","OFF"],["pFF_Child2_Light_Ceiling_Powered","OFF"],["pFF_Corridor_Light_Ceiling_Powered","OFF"],["pFF_Attic_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Shutter_Control","DOWN"],["pFF_Dressingroom_Shutter_Control","DOWN"],["pFF_Bedroom_Shutter_Control","DOWN"],["pFF_Child1_Shutter_Control","DOWN"],["pFF_Child2_Shutter_Control","DOWN"],["pFF_Attic_Shutter_Control","DOWN"]], "location_count": 2 },
    ],
    "enabled": [
        # **** ERDGESCHOSS incl. Schuppen ****
        { "phrase": u"licht gäste bad an", "items": [["pGF_Guesttoilet_Light_Ceiling_Powered","ON"],["pGF_Guesttoilet_Light_Mirror_Powered","ON"]] },
        { "phrase": u"deckenlicht gäste bad aus", "items": [["pGF_Guesttoilet_Light_Ceiling_Powered","OFF"]] },
        { "phrase": u"steckdose gäste bad aus", "items": [["pGF_Guesttoilet_Socket_Powered","OFF"]] },
        { "phrase": u"wc radio gäste bad ein", "items": [["pGF_Guesttoilet_Socket_Powered","ON"]] },
        { "phrase": u"rollladen gäste bad runter", "items": [["pGF_Guesttoilet_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden gäste bad rauf", "items": [["pGF_Guesttoilet_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es im gästeklo", "items": [["pGF_Guesttoilet_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie feucht ist es im gästeklo", "items": [["pGF_Guesttoilet_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"deckenlicht hwr aus", "items": [["pGF_Utilityroom_Light_Ceiling_Powered","OFF"]] },

        { "phrase": u"licht vorratsraum an", "items": [["pGF_Boxroom_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"wie kalt ist es im vorratsraum", "items": [["pGF_Boxroom_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie ist die Luftfeuchtigkeit im vorratsraum", "items": [["pGF_Boxroom_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht küche aus", "items": [[ "pGF_Kitchen_Light_Ceiling_Brightness", "OFF" ],["pGF_Kitchen_Light_Cupboard_Powered","OFF"]] },
        { "phrase": u"licht küche 50%", "items": [[ "pGF_Kitchen_Light_Ceiling_Brightness", "50" ]] },
        { "phrase": u"schranklicht küche an", "items": [["pGF_Kitchen_Light_Cupboard_Powered","ON"]] },
        { "phrase": u"rollladen küche schliessen", "items": [["pGF_Kitchen_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden küche hoch", "items": [["pGF_Kitchen_Shutter_Control","UP"]] },

        { "phrase": u"licht wohnzimmer stehlampe oben aus", "items": [["pGF_Livingroom_Light_Hue3_Color","OFF"]] },
        { "phrase": u"licht wohnzimmer stehlampe unten an", "items": [["pGF_Livingroom_Light_Hue2_Color","ON"]] },
        { "phrase": u"licht wohnzimmer stehlampe an", "items": [["pGF_Livingroom_Light_Hue2_Color","ON"],["pGF_Livingroom_Light_Hue3_Color","ON"]] },
        { "phrase": u"wohnzimmer stehlampe an", "items": [["pGF_Livingroom_Light_Hue2_Color","ON"],["pGF_Livingroom_Light_Hue3_Color","ON"]] },
        { "phrase": u"wohnzimmer couch steckdose an", "items": [["pGF_Livingroom_Socket_Couch_Powered","ON"]] },
        { "phrase": u"licht wohnzimmer bassbox an", "items": [["pGF_Livingroom_Light_Hue1_Color","ON"]] },
        { "phrase": u"licht wohnzimmer couch indirekt an", "items": [["pGF_Livingroom_Light_Hue1_Color","ON"],["pGF_Livingroom_Light_Hue2_Color","ON"],["pGF_Livingroom_Light_Hue3_Color","ON"]] },
        { "phrase": u"licht wohnzimmer couch decke an", "items": [["pGF_Livingroom_Light_Couchtable_Brightness","ON"]] },
        { "phrase": u"licht wohnzimmer couch an", "items": [["pGF_Livingroom_Light_Hue1_Color","ON"],["pGF_Livingroom_Light_Hue2_Color","ON"],["pGF_Livingroom_Light_Hue3_Color","ON"],["pGF_Livingroom_Light_Couchtable_Brightness","ON"]] },
        { "phrase": u"wohnzimmer bassbox steckdose an", "items": [["pGF_Livingroom_Socket_Bassbox_Powered","ON"]] },
        { "phrase": u"wohnzimmer kamin steckdose an", "items": [["pGF_Livingroom_Socket_Fireplace_Powered","ON"]] },
        { "phrase": u"licht wohnzimmer esstisch aus", "items": [["pGF_Livingroom_Light_Diningtable_Brightness","OFF"]] },
        { "phrase": u"licht wohnzimmer indirekt 30%", "items": [["pGF_Livingroom_Light_Hue1_Color","30"],["pGF_Livingroom_Light_Hue2_Color","30"],["pGF_Livingroom_Light_Hue3_Color","30"],["pGF_Livingroom_Light_Hue4_Color","30"],["pGF_Livingroom_Light_Hue5_Color","30"]] },
        { "phrase": u"licht wohnzimmer decke aus", "items": [["pGF_Livingroom_Light_Couchtable_Brightness","OFF"],["pGF_Livingroom_Light_Diningtable_Brightness","OFF"]] },
        { "phrase": u"licht wohnzimmer und steckdose bassbox an", "items": [["pGF_Livingroom_Light_Couchtable_Brightness","ON"],["pGF_Livingroom_Light_Diningtable_Brightness","ON"],["pGF_Livingroom_Light_Hue1_Color","ON"],["pGF_Livingroom_Light_Hue2_Color","ON"],["pGF_Livingroom_Light_Hue3_Color","ON"],["pGF_Livingroom_Light_Hue4_Color","ON"],["pGF_Livingroom_Light_Hue5_Color","ON"],["pGF_Livingroom_Socket_Bassbox_Powered","ON"]] },
        { "phrase": u"rollladen wohnzimmer schliessen", "items": [["pGF_Livingroom_Shutter_Terrace_Control","DOWN"],["pGF_Livingroom_Shutter_Couch_Control","DOWN"]] },
        { "phrase": u"rollläden wohnzimmer couch hoch", "items": [["pGF_Livingroom_Shutter_Couch_Control","UP"]] },
        { "phrase": u"rollläden wohnzimmer esstisch runter", "items": [["pGF_Livingroom_Shutter_Terrace_Control","DOWN"]] },
        { "phrase": u"rollläden wohnzimmer terasse runter", "items": [["pGF_Livingroom_Shutter_Terrace_Control","DOWN"]] },
        { "phrase": u"wie warm ist es im wohnzimmer", "items": [["pGF_Livingroom_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie trocken ist es im wohnzimmer", "items": [["pGF_Livingroom_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht gästezimmer an", "items": [["pGF_Guestroom_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"licht bastelzimmer an", "items": [["pGF_Guestroom_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"rollladen gästezimmer schliessen", "items": [["pGF_Guestroom_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden gästezimmer hoch", "items": [["pGF_Guestroom_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es im gästezimmer", "items": [["pGF_Guestroom_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie feucht ist es im gästezimmer", "items": [["pGF_Guestroom_Air_Sensor_Humidity_Value","READ"]] },

        # TODO should exclude upper floor light
        { "phrase": u"flur deckenlampe aus", "items": [["pFF_Corridor_Light_Ceiling_Powered","OFF"],["pGF_Corridor_Light_Ceiling_Powered","OFF"]], "location_count": 2 },
        { "phrase": u"flur spiegel licht aus", "items": [[ "pGF_Corridor_Light_Mirror_Powered", "OFF" ]], "location_count": 2 },
        { "phrase": u"flur indirekt aus", "items": [[ "pGF_Corridor_Light_Hue_Color", "OFF" ]], "location_count": 2 },
        # TODO should exclude upper floor light
        { "phrase": u"licht flur an", "items": [["pFF_Corridor_Light_Ceiling_Powered","ON"],["pGF_Corridor_Light_Ceiling_Powered","ON"],["pGF_Corridor_Light_Mirror_Powered","ON"],["pGF_Corridor_Light_Hue_Color","ON"]], "location_count": 2 },
        { "phrase": u"wie warm ist es im flur", "items": [["pGF_Corridor_Air_Sensor_Temperature_Value","READ"],["pFF_Corridor_Air_Sensor_Temperature_Value","READ"]], "location_count": 2 },
        { "phrase": u"wie warm ist es im flur unten", "items": [["pGF_Corridor_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie feucht ist es im flur unten", "items": [["pGF_Corridor_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"deckenlicht garage aus", "items": [["pGF_Garage_Light_Ceiling_Powered","OFF"]], "location_count": 3 },
        { "phrase": u"deckenlicht schuppen an", "items": [["pGF_Garage_Light_Ceiling_Powered","ON"]], "location_count": 3 },
        # TODO should exclude outdoor light
        { "phrase": u"licht schuppen an", "items": [["pOutdoor_Streedside_Garage_Light_Powered","ON"],["pOutdoor_Garden_Garage_Light_Powered","ON"],["pGF_Garage_Light_Ceiling_Powered","ON"]], "location_count": 3 },
        { "phrase": u"wie warm ist es im schuppen", "items": [["pGF_Garage_Air_Sensor_Temperature_Value","READ"]], "location_count": 3 },
        { "phrase": u"wie feucht ist es in der garage", "items": [["pGF_Garage_Air_Sensor_Humidity_Value","READ"]], "location_count": 3 },

        { "phrase": u"licht untergeschoss aus", "items": [["pGF_Livingroom_Light_Hue1_Color","OFF"],["pGF_Livingroom_Light_Hue2_Color","OFF"],["pGF_Livingroom_Light_Hue3_Color","OFF"],["pGF_Livingroom_Light_Hue4_Color","OFF"],["pGF_Livingroom_Light_Hue5_Color","OFF"],["pGF_Corridor_Light_Ceiling_Powered","OFF"],["pGF_Boxroom_Light_Ceiling_Powered","OFF"],["pGF_Guesttoilet_Light_Mirror_Powered","OFF"],["pGF_Guestroom_Light_Ceiling_Powered","OFF"],["pGF_Livingroom_Light_Couchtable_Brightness","OFF"],["pGF_Utilityroom_Light_Ceiling_Powered","OFF"],["pGF_Guesttoilet_Light_Ceiling_Powered","OFF"],["pGF_Kitchen_Light_Ceiling_Brightness","OFF"],["pGF_Kitchen_Light_Cupboard_Powered","OFF"],["pGF_Livingroom_Light_Diningtable_Brightness","OFF"],["pGF_Corridor_Light_Mirror_Powered","OFF"],["pGF_Corridor_Light_Hue_Color","OFF"],["pGF_Garage_Light_Ceiling_Powered","OFF"]] },        
        
        # **** OBERGESCHOSS incl. Dachboden ****

        { "phrase": u"licht bad aus", "items": [["pFF_Bathroom_Light_Mirror_Powered","OFF"],["pFF_Bathroom_Light_Ceiling_Powered","OFF"]] },
        { "phrase": u"deckenlicht badezimmer an", "items": [[ "pFF_Bathroom_Light_Ceiling_Powered", "ON" ]] },
        { "phrase": u"rollladen badezimmer schliessen", "items": [["pFF_Bathroom_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden badezimmer hoch", "items": [["pFF_Bathroom_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es im bad", "items": [["pFF_Bathroom_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie feucht ist es im bad", "items": [["pFF_Bathroom_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht ankleide an", "items": [["pFF_Dressingroom_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"rollladen ankleide schliessen", "items": [["pFF_Dressingroom_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden ankleide hoch", "items": [["pFF_Dressingroom_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es in der ankleide", "items": [["pFF_Dressingroom_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie feucht ist es in der ankleide", "items": [["pFF_Dressingroom_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht schlafzimmer bett links und decke an", "items": [[ "pFF_Bedroom_Light_Hue_Left_Color", "ON" ],[ "pFF_Bedroom_Light_Ceiling_Powered", "ON" ]] },
        { "phrase": u"licht schlafzimmer bett links und rechts an", "items": [[ "pFF_Bedroom_Light_Hue_Left_Color", "ON" ],[ "pFF_Bedroom_Light_Hue_Right_Color", "ON" ]] },
        { "phrase": u"deckenlicht schlafzimmer an", "items": [[ "pFF_Bedroom_Light_Ceiling_Powered", "ON" ]] },
        { "phrase": u"rollladen schlafzimmer schliessen", "items": [["pFF_Bedroom_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden schlafzimmer hoch", "items": [["pFF_Bedroom_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es im schlafzimmer", "items": [["pFF_Bedroom_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie trocken ist es im schlafzimmer", "items": [["pFF_Bedroom_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht sportzimmer an", "items": [["pFF_Child1_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"rollladen sportzimmer schliessen", "items": [["pFF_Child1_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden sportzimmer hoch", "items": [["pFF_Child1_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es im sportzimmer", "items": [["pFF_Child1_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie trocken ist es im sportzimmer zimmer", "items": [["pFF_Child1_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht schminkzimmer aus", "items": [["pFF_Child2_Light_Ceiling_Powered","OFF"]] },
        { "phrase": u"rollladen schminkzimmer schliessen", "items": [["pFF_Child2_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden schminkzimmer hoch", "items": [["pFF_Child2_Shutter_Control","UP"]] },
        { "phrase": u"wie warm ist es im schminkzimmer", "items": [["pFF_Child2_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie trocken ist es im schminkzimmer zimmer", "items": [["pFF_Child2_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht flur obergeschoss an", "items": [["pFF_Corridor_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"wie warm ist es im flur oben", "items": [["pFF_Corridor_Air_Sensor_Temperature_Value","READ"]] },

        { "phrase": u"licht dachboden an", "items": [["pFF_Attic_Light_Ceiling_Powered","ON"]] },
        { "phrase": u"steckdose dachboden aus", "items": [["pFF_Attic_Socket_Powered","OFF"]] },
        { "phrase": u"rollladen dachboden schliessen", "items": [["pFF_Attic_Shutter_Control","DOWN"]] },
        { "phrase": u"rollläden dachboden hoch", "items": [["pFF_Attic_Shutter_Control","UP"]] },
        { "phrase": u"wie kalt ist es auf dem dachboden", "items": [["pFF_Attic_Air_Sensor_Temperature_Value","READ"]] },
        { "phrase": u"wie trocken ist es auf dem dachboden", "items": [["pFF_Attic_Air_Sensor_Humidity_Value","READ"]] },

        { "phrase": u"licht obergeschoss an", "items": [["pFF_Bathroom_Light_Mirror_Powered","ON"],["pFF_Dressingroom_Light_Ceiling_Powered","ON"],["pFF_Bedroom_Light_Ceiling_Powered","ON"],["pFF_Corridor_Light_Ceiling_Powered","ON"],["pFF_Child2_Light_Ceiling_Powered","ON"],["pFF_Bedroom_Light_Hue_Right_Color","ON"],["pFF_Bedroom_Light_Hue_Left_Color","ON"],["pFF_Bathroom_Light_Ceiling_Powered","ON"],["pFF_Child1_Light_Ceiling_Powered","ON"],["pFF_Attic_Light_Ceiling_Powered","ON"]] },

        # **** Draussen (Garten) ****
        
        { "phrase": u"licht schuppen vorne an", "items": [["pOutdoor_Streedside_Garage_Light_Powered","ON"]] },
        { "phrase": u"licht haustür an", "items": [["pOutdoor_Streedside_Frontdoor_Light_Powered","ON"]] },
        { "phrase": u"licht carport an", "items": [["pOutdoor_Carport_Light_Powered","ON"]] },
        { "phrase": u"licht terasse an", "items": [["pOutdoor_Garden_Terrace_Light_Brightness","ON"]] },
        { "phrase": u"licht schuppen hinten an", "items": [["pOutdoor_Garden_Garage_Light_Powered","ON"]] },

        { "phrase": u"aussensteckdosen vorne an", "items": [[ "pOutdoor_Streeside_Socket_Powered", "ON" ]] },
        { "phrase": u"aussensteckdosen hinten aus", "items": [[ "pOutdoor_Garden_Terrace_Socket_Powered", "OFF" ]] },
        { "phrase": u"aussensteckdosen an", "items": [[ "pOutdoor_Streeside_Socket_Powered", "ON" ],[ "pOutdoor_Garden_Terrace_Socket_Powered", "ON" ]] },
        { "phrase": u"steckdosen draussen aus", "items": [[ "pOutdoor_Streeside_Socket_Powered", "OFF" ],[ "pOutdoor_Garden_Terrace_Socket_Powered", "OFF" ]] },
        
        { "phrase": u"wie kalt ist es im garten", "items": [["pOutdoor_WeatherStation_Temperature","READ"]] },
        { "phrase": u"wie ist die luftfeuchtigkeit im garten", "items": [["pOutdoor_WeatherStation_Humidity","READ"]] },
        
        # **** HUE COLOR LIGHTS ****
        { "phrase": u"farbtemperatur wohnzimmer stehlampe oben warmweiss", "items": [["pGF_Livingroom_Light_Hue3_Temperature","100"]] },
        { "phrase": u"farbtemperatur wohnzimmer stehlampe 50%", "items": [["pGF_Livingroom_Light_Hue2_Temperature","50"],["pGF_Livingroom_Light_Hue3_Temperature","50"]] },
        { "phrase": u"farbtemperatur wohnzimmer kaltweiß", "items": [["pGF_Livingroom_Light_Hue5_Temperature","0"],["pGF_Livingroom_Light_Hue4_Temperature","0"],["pGF_Livingroom_Light_Hue2_Temperature","0"],["pGF_Livingroom_Light_Hue3_Temperature","0"],["pGF_Livingroom_Light_Hue1_Temperature","0"]] },
        
        { "phrase": u"licht wohnzimmer stehlampe oben rot", "items": [["pGF_Livingroom_Light_Hue3_Color","0,100,100"]] },
        { "phrase": u"wohnzimmer farbe blau", "items": [["pGF_Livingroom_Light_Hue4_Color","240,100,100"],["pGF_Livingroom_Light_Hue1_Color","240,100,100"],["pGF_Livingroom_Light_Hue5_Color","240,100,100"],["pGF_Livingroom_Light_Hue2_Color","240,100,100"],["pGF_Livingroom_Light_Hue3_Color","240,100,100"]] },
        { "phrase": u"wohnzimmer lichtfarbe grün", "items": [["pGF_Livingroom_Light_Hue4_Color","120,100,50"],["pGF_Livingroom_Light_Hue1_Color","120,100,50"],["pGF_Livingroom_Light_Hue5_Color","120,100,50"],["pGF_Livingroom_Light_Hue2_Color","120,100,50"],["pGF_Livingroom_Light_Hue3_Color","120,100,50"]] },

        # **** Sonstiges ****
        
        { "phrase": u"aufstehen", "items": [[ "pOther_Scene2", "ON" ]] },
        { "phrase": u"schlafen gehen", "items": [[ "pOther_Scene3", "ON" ]] },
        { "phrase": u"gute nacht", "items": [[ "pOther_Scene4", "ON" ]] },

        # **** Opener Questions ****
        { "phrase": u"ist das fenster im wohnzimmer offen", "items": [["pGF_Livingroom_Openingcontact_Window_Couch_State","READ"],["pGF_Livingroom_Openingcontact_Window_Terrace_State","READ"]] },
        { "phrase": u"sind die fenster im wohnzimmer offen", "items": [["pGF_Livingroom_Openingcontact_Window_Couch_State","READ"],["pGF_Livingroom_Openingcontact_Window_Terrace_State","READ"]] },
        { "phrase": u"ist das terassen fenster im wohnzimmer offen", "items": [["pGF_Livingroom_Openingcontact_Window_Terrace_State","READ"]] },
        #{ "phrase": u"welche fenster sind offen", "items": [] },
        #{ "phrase": u"welches fenster ist offen", "items": [] },
        #{ "phrase": u"welche türen sind offen", "items": [] },
        #{ "phrase": u"welche tür ist offen", "items": [] },
        
        # **** Opener Questions ****
        { "phrase": u"ist der rollladen im wohnzimmer offen", "items": [["pGF_Livingroom_Shutter_Terrace_Control","READ"],["pGF_Livingroom_Shutter_Couch_Control","READ"]] },
        { "phrase": u"ist der terassen rollladen im wohnzimmer offen", "items": [["pGF_Livingroom_Shutter_Terrace_Control","READ"]] },
        
        # **** LIGHT QUESTIONS ****
        { "phrase": u"ist das couch deckenlicht im wohnzimmer an", "items": [["pGF_Livingroom_Light_Couchtable_Brightness","READ"]] },
        { "phrase": u"ist das flur spiegel licht an", "items": [["pGF_Corridor_Light_Mirror_Powered","READ"]], "location_count": 2 },
        
        # **** percentage check ****

        { "phrase": u"licht küche 50% prozent", "items": [[ "pGF_Kitchen_Light_Ceiling_Brightness", "50" ]] },
        { "phrase": u"licht küche fünfzig prozent", "items": [[ "pGF_Kitchen_Light_Ceiling_Brightness", "50" ]] },
        { "phrase": u"licht wohnzimmer indirekt x prozent", "items": [], "is_valid": False },
        
        # **** ELECTRONIC GADGETS ****        

        #{ "phrase": u"wohnzimmer fernseher kanal fünf", "items": [[ "SAT_KEY_PRO7", "DEFAULT_ON" ]] },
        #{ "phrase": u"wohnzimmer fernseher an", "items": [[ "Scene6", "ACTION_ON" ]] },
        #{ "phrase": u"wohnzimmer fernseher kanal drei", "items": [[ "SAT_KEY_RTL", "DEFAULT_ON" ]] },
        #{ "phrase": u"wohnzimmer licht und fernseher an", "items": [[ "Light_FF_Livingroom_Couch", "ACTION_ON" ],[ "Light_FF_Livingroom_Diningtable", "ACTION_ON" ],[ "Scene6", "ACTION_ON" ]] },
        
        { "phrase": u"wie ist das internet im flur", "items": [["pGF_Corridor_Fritzbox_DslDownstreamAttenuation","READ"],["pGF_Corridor_Fritzbox_DslDownstreamNoiseMargin","READ"],["pGF_Corridor_Fritzbox_DslUpstreamAttenuation","READ"],["pGF_Corridor_Fritzbox_GuestWifi","READ"],["pGF_Corridor_Speedtest_UpstreamRate","READ"],["pGF_Corridor_Fritzbox_DslCRCErrors","READ"],["pGF_Corridor_Fritzbox_DslEnable","READ"],["pGF_Corridor_Fritzbox_DslUpstreamNoiseMargin","READ"],["pGF_Corridor_Fritzbox_DslFECErrors","READ"],["pGF_Corridor_Speedtest_Start","READ"],["pGF_Corridor_Fritzbox_DslDownstreamCurrRate","READ"],["pGF_Corridor_Fritzbox_Uptime","READ"],["pGF_Corridor_Fritzbox_DslDownstreamMaxRate","READ"],["pGF_Corridor_Speedtest_DownstreamRate","READ"],["pGF_Corridor_Fritzbox_DslUpstreamCurrRate","READ"],["pGF_Corridor_Fritzbox_DslStatus","READ"],["pGF_Corridor_Fritzbox_DslHECErrors","READ"]], "location_count": 2 },

        # **** FALSE POSITIVES ****
        
        { "phrase": u"wie warm ist es im schlafzimmer und in der küche", "items": [[ "pFF_Bedroom_Air_Sensor_Temperature_Value", "READ" ]], "is_valid": False, "location_count": 2 },
        { "phrase": u"flur obergeschoss 50%", "items": [], "is_valid": False },

        # **** CLIENT ID BASED ****

        { "phrase": u"wohnzimmer stehlampe unten aus", "items": [["pGF_Livingroom_Light_Hue2_Color","OFF"]]},
        { "phrase": u"stehlampe unten aus", "client_id": "amzn1.ask.device.AFUSC2ZJY7NS7773FR5SXTQXXG65WQS724EL6IDBRKBGJWEFHXMN7L5IBA6DDDUSH27MYRGPKJTGIN75I7S5BI3P56JLBDCCXRHWJJPRNY7BKABQPTX2K4ZYA5DIMH4BWWCAEV5TFVVK73CCJROPZWG3IUZ4U22ITRXFWVY4BUWODEM6OVO6G", "items": [["pGF_Livingroom_Light_Hue2_Color","OFF"]] },
        { "phrase": u"licht decken lampe aus", "client_id": "amzn1.ask.device.AFUSC2ZJY7NS7773FR5SXTQXXG65WQS724EL6IDBRKBGJWEFHXMN7L5IBA6DDDUSH27MYRGPKJTGIN75I7S5BI3P56JLBDCCXRHWJJPRNY7BKABQPTX2K4ZYA5DIMH4BWWCAEV5TFVVK73CCJROPZWG3IUZ4U22ITRXFWVY4BUWODEM6OVO6G", "items": [["pGF_Livingroom_Light_Diningtable_Brightness","OFF"],["pGF_Livingroom_Light_Couchtable_Brightness","OFF"]] },
        
        
        { "phrase": u"steckdose bassbox aus", "client_id": "amzn1.ask.device.AFUSC2ZJY7NS7773FR5SXTQXXG65WQS724EL6IDBRKBGJWEFHXMN7L5IBA6DDDUSH27MYRGPKJTGIN75I7S5BI3P56JLBDCCXRHWJJPRNY7BKABQPTX2K4ZYA5DIMH4BWWCAEV5TFVVK73CCJROPZWG3IUZ4U22ITRXFWVY4BUWODEM6OVO6G", "items": [["pGF_Livingroom_Socket_Bassbox_Powered","OFF"]] },
        #{ "phrase": u"fernseher an", "client_id": "amzn1.ask.device.AFUSC2ZJY7NS7773FR5SXTQXXG65WQS724EL6IDBRKBGJWEFHXMN7L5IBA6DDDUSH27MYRGPKJTGIN75I7S5BI3P56JLBDCCXRHWJJPRNY7BKABQPTX2K4ZYA5DIMH4BWWCAEV5TFVVK73CCJROPZWG3IUZ4U22ITRXFWVY4BUWODEM6OVO6G", "items": [[ "Scene6", "ACTION_ON" ]] },
        { "phrase": u"licht flur oben an und küche 50%", "client_id": "amzn1.ask.device.AFUSC2ZJY7NS7773FR5SXTQXXG65WQS724EL6IDBRKBGJWEFHXMN7L5IBA6DDDUSH27MYRGPKJTGIN75I7S5BI3P56JLBDCCXRHWJJPRNY7BKABQPTX2K4ZYA5DIMH4BWWCAEV5TFVVK73CCJROPZWG3IUZ4U22ITRXFWVY4BUWODEM6OVO6G", "items": [["pFF_Corridor_Light_Ceiling_Powered","ON"],["pGF_Kitchen_Light_Ceiling_Brightness","50"]], "location_count": 2 },
        
        # **** Kombiniert ****
        
        { "phrase": u"licht flur oben und wohnzimmer an", "items": [[ "pGF_Livingroom_Light_Hue4_Color", "ON" ],[ "pGF_Livingroom_Light_Hue5_Color", "ON" ],[ "pGF_Livingroom_Light_Hue3_Color", "ON" ],[ "pGF_Livingroom_Light_Hue1_Color", "ON" ],[ "pGF_Livingroom_Light_Hue2_Color", "ON" ],[ "pGF_Livingroom_Light_Couchtable_Brightness", "ON" ],[ "pGF_Livingroom_Light_Diningtable_Brightness", "ON" ],[ "pFF_Corridor_Light_Ceiling_Powered", "ON" ]], "location_count": 2 },
        { "phrase": u"licht flur oben und wohnzimmer und küche an", "items": [[ "pGF_Livingroom_Light_Hue4_Color", "ON" ],[ "pGF_Livingroom_Light_Hue5_Color", "ON" ],[ "pGF_Livingroom_Light_Hue3_Color", "ON" ],[ "pGF_Livingroom_Light_Hue1_Color", "ON" ],[ "pGF_Livingroom_Light_Hue2_Color", "ON" ],[ "pGF_Livingroom_Light_Couchtable_Brightness", "ON" ],[ "pGF_Livingroom_Light_Diningtable_Brightness", "ON" ],[ "pFF_Corridor_Light_Ceiling_Powered", "ON" ],[ "pGF_Kitchen_Light_Ceiling_Brightness", "ON" ],[ "pGF_Kitchen_Light_Cupboard_Powered", "ON" ]], "location_count": 3 },
        { "phrase": u"licht wohnzimmer und küche 50%", "items": [[ "pGF_Livingroom_Light_Hue4_Color", "50" ],[ "pGF_Livingroom_Light_Hue5_Color", "50" ],[ "pGF_Livingroom_Light_Hue3_Color", "50" ],[ "pGF_Livingroom_Light_Hue1_Color", "50" ],[ "pGF_Livingroom_Light_Hue2_Color", "50" ],[ "pGF_Livingroom_Light_Couchtable_Brightness", "50" ],[ "pGF_Livingroom_Light_Diningtable_Brightness", "50" ],[ "pGF_Kitchen_Light_Ceiling_Brightness", "50" ]], "location_count": 2 },
        { "phrase": u"licht wohnzimmer 50% und küche an", "items": [[ "pGF_Livingroom_Light_Hue4_Color", "50" ],[ "pGF_Livingroom_Light_Hue5_Color", "50" ],[ "pGF_Livingroom_Light_Hue3_Color", "50" ],[ "pGF_Livingroom_Light_Hue1_Color", "50" ],[ "pGF_Livingroom_Light_Hue2_Color", "50" ],[ "pGF_Livingroom_Light_Couchtable_Brightness", "50" ],[ "pGF_Livingroom_Light_Diningtable_Brightness", "50" ],[ "pGF_Kitchen_Light_Ceiling_Brightness", "ON" ],[ "pGF_Kitchen_Light_Cupboard_Powered", "ON" ]], "location_count": 2 },
        { "phrase": u"licht wohnzimmer an und rollladen küche runter", "items": [[ "pGF_Livingroom_Light_Hue4_Color", "ON" ],[ "pGF_Livingroom_Light_Hue5_Color", "ON" ],[ "pGF_Livingroom_Light_Hue3_Color", "ON" ],[ "pGF_Livingroom_Light_Hue1_Color", "ON" ],[ "pGF_Livingroom_Light_Hue2_Color", "ON" ],[ "pGF_Livingroom_Light_Couchtable_Brightness", "ON" ],[ "pGF_Livingroom_Light_Diningtable_Brightness", "ON" ],[ "pGF_Kitchen_Shutter_Control", "DOWN" ]], "location_count": 2 },
        { "phrase": u"licht wohnzimmer und flur an und dachboden und bad rollläden runter", "items": [[ "pGF_Livingroom_Light_Hue4_Color", "ON" ],[ "pGF_Corridor_Light_Ceiling_Powered", "ON" ],[ "pGF_Livingroom_Light_Hue5_Color", "ON" ],[ "pFF_Corridor_Light_Ceiling_Powered", "ON" ],[ "pGF_Livingroom_Light_Hue3_Color", "ON" ],[ "pGF_Livingroom_Light_Hue1_Color", "ON" ],[ "pGF_Livingroom_Light_Couchtable_Brightness", "ON" ],[ "pGF_Livingroom_Light_Diningtable_Brightness", "ON" ],[ "pGF_Livingroom_Light_Hue2_Color", "ON" ],[ "pGF_Corridor_Light_Mirror_Powered", "ON" ],[ "pGF_Corridor_Light_Hue_Color", "ON" ],[ "pFF_Bathroom_Shutter_Control", "DOWN" ],[ "pFF_Attic_Shutter_Control", "DOWN" ]], "location_count": 5 },
        { "phrase": u"alle licht aus und rollläden komplett runter", "items": [["pGF_Guesttoilet_Light_Ceiling_Powered","OFF"],["pGF_Guesttoilet_Light_Mirror_Powered","OFF"],["pGF_Utilityroom_Light_Ceiling_Powered","OFF"],["pGF_Boxroom_Light_Ceiling_Powered","OFF"],["pGF_Kitchen_Light_Ceiling_Brightness","OFF"],["pGF_Kitchen_Light_Cupboard_Powered","OFF"],["pGF_Livingroom_Light_Diningtable_Brightness","OFF"],["pGF_Livingroom_Light_Hue4_Color","OFF"],["pGF_Livingroom_Light_Hue5_Color","OFF"],["pGF_Livingroom_Light_Hue1_Color","OFF"],["pGF_Livingroom_Light_Hue2_Color","OFF"],["pGF_Livingroom_Light_Hue3_Color","OFF"],["pGF_Livingroom_Light_Couchtable_Brightness","OFF"],["pGF_Guestroom_Light_Ceiling_Powered","OFF"],["pGF_Corridor_Light_Hue_Color","OFF"],["pGF_Corridor_Light_Mirror_Powered","OFF"],["pGF_Corridor_Light_Ceiling_Powered","OFF"],["pGF_Garage_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Light_Mirror_Powered","OFF"],["pFF_Dressingroom_Light_Ceiling_Powered","OFF"],["pFF_Bedroom_Light_Hue_Right_Color","OFF"],["pFF_Bedroom_Light_Hue_Left_Color","OFF"],["pFF_Bedroom_Light_Ceiling_Powered","OFF"],["pFF_Child1_Light_Ceiling_Powered","OFF"],["pFF_Child2_Light_Ceiling_Powered","OFF"],["pFF_Corridor_Light_Ceiling_Powered","OFF"],["pFF_Attic_Light_Ceiling_Powered","OFF"],["pGF_Guesttoilet_Shutter_Control","DOWN"],["pGF_Kitchen_Shutter_Control","DOWN"],["pGF_Livingroom_Shutter_Terrace_Control","DOWN"],["pGF_Livingroom_Shutter_Couch_Control","DOWN"],["pGF_Guestroom_Shutter_Control","DOWN"],["pFF_Bathroom_Shutter_Control","DOWN"],["pFF_Dressingroom_Shutter_Control","DOWN"],["pFF_Bedroom_Shutter_Control","DOWN"],["pFF_Child1_Shutter_Control","DOWN"],["pFF_Child2_Shutter_Control","DOWN"],["pFF_Attic_Shutter_Control","DOWN"]] },
        { "phrase": u"licht innen aus und rollläden obergeschoss runter", "items": [["pGF_Guesttoilet_Light_Ceiling_Powered","OFF"],["pGF_Guesttoilet_Light_Mirror_Powered","OFF"],["pGF_Utilityroom_Light_Ceiling_Powered","OFF"],["pGF_Boxroom_Light_Ceiling_Powered","OFF"],["pGF_Kitchen_Light_Ceiling_Brightness","OFF"],["pGF_Kitchen_Light_Cupboard_Powered","OFF"],["pGF_Livingroom_Light_Diningtable_Brightness","OFF"],["pGF_Livingroom_Light_Hue4_Color","OFF"],["pGF_Livingroom_Light_Hue5_Color","OFF"],["pGF_Livingroom_Light_Hue1_Color","OFF"],["pGF_Livingroom_Light_Hue2_Color","OFF"],["pGF_Livingroom_Light_Hue3_Color","OFF"],["pGF_Livingroom_Light_Couchtable_Brightness","OFF"],["pGF_Guestroom_Light_Ceiling_Powered","OFF"],["pGF_Corridor_Light_Hue_Color","OFF"],["pGF_Corridor_Light_Mirror_Powered","OFF"],["pGF_Corridor_Light_Ceiling_Powered","OFF"],["pGF_Garage_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Light_Mirror_Powered","OFF"],["pFF_Dressingroom_Light_Ceiling_Powered","OFF"],["pFF_Bedroom_Light_Hue_Right_Color","OFF"],["pFF_Bedroom_Light_Hue_Left_Color","OFF"],["pFF_Bedroom_Light_Ceiling_Powered","OFF"],["pFF_Child1_Light_Ceiling_Powered","OFF"],["pFF_Child2_Light_Ceiling_Powered","OFF"],["pFF_Corridor_Light_Ceiling_Powered","OFF"],["pFF_Attic_Light_Ceiling_Powered","OFF"],["pFF_Bathroom_Shutter_Control","DOWN"],["pFF_Dressingroom_Shutter_Control","DOWN"],["pFF_Bedroom_Shutter_Control","DOWN"],["pFF_Child1_Shutter_Control","DOWN"],["pFF_Child2_Shutter_Control","DOWN"],["pFF_Attic_Shutter_Control","DOWN"]], "location_count": 2 },
        { "phrase": u"licht im wohnzimmer und aussen licht und steckdosen aus", "items": [["pGF_Livingroom_Light_Diningtable_Brightness","OFF"],["pGF_Livingroom_Light_Hue4_Color","OFF"],["pGF_Livingroom_Light_Hue5_Color","OFF"],["pGF_Livingroom_Light_Hue1_Color","OFF"],["pGF_Livingroom_Light_Hue2_Color","OFF"],["pGF_Livingroom_Light_Hue3_Color","OFF"],["pGF_Livingroom_Light_Couchtable_Brightness","OFF"],["pOutdoor_Streedside_Garage_Light_Powered","OFF"],["pOutdoor_Streedside_Frontdoor_Light_Powered","OFF"],["pOutdoor_Carport_Light_Powered","OFF"],["pOutdoor_Garden_Garage_Light_Powered","OFF"],["pOutdoor_Garden_Terrace_Light_Brightness","OFF"],["pOutdoor_Streeside_Socket_Powered","OFF"],["pOutdoor_Garden_Terrace_Socket_Powered","OFF"]], "location_count": 2 },
        { "phrase": u"wie ist die temperatur im schlafzimmer und die luftfeuchtigkeit wohnzimmer", "items": [["pGF_Livingroom_Air_Sensor_Humidity_Value","READ"],["pFF_Bedroom_Air_Sensor_Temperature_Value","READ"]], "location_count": 2 },
        { "phrase": u"wie warm ist es im schlafzimmer und im wohnzimmer", "items": [["pFF_Bedroom_Air_Sensor_Temperature_Value","READ"],["pGF_Livingroom_Air_Sensor_Temperature_Value","READ"]], "location_count": 2 },
    ]
} 
