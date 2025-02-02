# serial ports +++++++++++++++++++
port_vitoconnect = None  # '/dev/ttyS0'  older Pi:'/dev/ttyAMA0'  {optional} set None if no Vitoconnect
port_optolink = '/dev/ttyOptolink'   # '/dev/ttyUSB0'  {mandatory}

vs2timeout = 120                 # seconds to detect VS2 protocol on vitoconnect connection


# MQTT +++++++++++++++++++
mqtt = "mosquitto:1883"          # e.g. "192.168.0.123:1883"; set None to disable MQTT
mqtt_user = None                 # "<user>:<pwd>"; set None for anonymous connect
mqtt_topic = "optolink"          # "optolink"
mqtt_fstr = "{dpname}"           # "{dpaddr:04X}_{dpname}"
mqtt_listen = "optolink/cmnd"    # "optolink/cmnd"; set None to disable listening
mqtt_respond = "optolink/resp"   # "optolink/resp"


# TCP/IP +++++++++++++++++++
tcpip_port = None         # e.g. 65234 is used by Viessdataby default; set None to disable TCP/IP


# full raw timing
fullraw_eot_time = 0.05    # seconds. time no receive to decide end of telegram
fullraw_timeout = 2        # seconds. timeout, return in any case
olbreath = 0.1             # seconds of sleep after request-response cycle

# logging, info +++++++++++++++++++
log_vitoconnect = False    # logs communication with Vitoconnect (rx+tx telegrams)
show_opto_rx = False        # display on screen (no output when ran as service)

# format +++++++++++++++++++
max_decimals = 1
data_hex_format = '02x'    # set to '02X' for capitals
resp_addr_format = '04x'     # format of DP address in MQTT/TCPIP request response; e.g. 'd': decimal, '04X': hex 4 digits

# Viessdata utils +++++++++++++++++++
write_viessdata_csv = False
viessdata_csv_path = ""
buffer_to_write = 60
dec_separator = ","

# 1-wire sensors +++++++++++++++++++
w1sensors = {}


# polling datapoints +++++++++++++++++++
poll_interval = 60      # seconds. 0 for continuous, set -1 to disable Polling
poll_items = [
    # ([PollCycle,] Name, DpAddr, Len, Scale/Type, Signed)
    ("getBetriebsart", 0x2323, 1, 1), #0,1,2,3,4	Abschalt,Nur WW,Heizen + WW,Dauernd Reduziert,Dauernd Normal
    ("getLeistungIst", 0xA38F, 1, 0.5),
    ("getHeizkreisPumpeDrehzahl", 0x7663, 2, 'b:1:2'),
    ("getTempRaumSoll", 0x2306, 1, 1),
    ("getTempAussen", 0x5525, 2, 0.1, True),
    ("getTempAussenGedaempft", 0x5527, 2, 0.1, True),
    ("getTempVorlaufSoll", 0x2544, 2, 0.1, True),
    ("getTempVorlauf", 0x2900, 2, 0.1, True),
    ("getTempKesselSoll", 0x555A, 2, 0.1, True),
    ("getTempKessel", 0x0810, 2, 0.1, True),
    ("getBrennerStarts", 0x088A, 4, 1),
    ("getBrennerStunden", 0x08A7, 4, 0.000277777777778),
    ("getTempWasserSpeicher", 0x0812, 2, 0.1, True),
    ("getTempSolarKollektor", 0x6564, 2, 0.1, True),
    ("getTempSolarSpeicher", 0x6566, 2, 0.1, True),
    ("getSolarStunden", 0x6568, 2, 1),
    ("getSolarLeistung", 0x6560, 4, 1),
    ("getSolarPumpeStatus", 0x6552, 1, 1),
    ("getNachladeunterdrueckungStatus", 0x6551, 1, 1),
    ("getSammelstoerung", 0x0A82, 1),
]

