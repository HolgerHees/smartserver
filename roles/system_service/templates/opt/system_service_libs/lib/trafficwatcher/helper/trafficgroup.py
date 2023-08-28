class TrafficGroup():
    NORMAL = 'normal'
    OBSERVED = 'observed'
    SCANNING = 'scanning'
    INTRUDED = 'intruded'

    PRIORITY = {
        NORMAL: 0,
        OBSERVED: 1,
        SCANNING: 2,
        INTRUDED: 3
    }
