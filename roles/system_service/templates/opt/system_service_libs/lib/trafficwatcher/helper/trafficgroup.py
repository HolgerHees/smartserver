class TrafficGroup():
    NORMAL = 'normal'
    OBSERVED = 'observed'
    SCANNING = 'scanning'
    INTRUDED = 'intruded'

    PRIORITY = {
        "-": 0,
        NORMAL: 1,
        OBSERVED: 2,
        SCANNING: 3,
        INTRUDED: 4
    }
