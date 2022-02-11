class ArgsParser():
    @staticmethod
    def setParameter(parameter, config, key,value):
        if key in config:
            if type(config[key]) == type(True):
                parameter[key] = True if value == "yes" else False
            else:
                parameter[key] = value
    
    @staticmethod
    def parse(config, argv):
        parameter = dict(config)
        
        i = 1
        while i < len(argv):
            arg = argv[i].lstrip("-")
            arg = arg.split("=")
            if len(arg)>1:
                ArgsParser.setParameter(parameter, config, arg[0], arg[1] )
            else:
                for key in parameter:
                    if arg == "--{}".format(key) and i + 1 < len(argv):
                        ArgsParser.setParameter(parameter, config, key, argv[i+1] )
                        i += 1
                        break
            i += 1
            
        return parameter
