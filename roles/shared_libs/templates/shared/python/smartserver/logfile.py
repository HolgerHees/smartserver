import re

from datetime import datetime

class LogFile:
    def __init__(self,file):
        self.file = file
        self.new_line =  None
        self.active_colors = []
        self.cleaned_color = False
        
    def write(self,text):
        try:
            text = text.decode("utf-8")
        except AttributeError:
            pass

        # clean linefeeds
        text = text.replace("\r\n","\n")

        # handle carriage return
        text = text.replace("\r\x1b[K","\n")
        text = text.replace("\r","\n")

        lines = text.split("\n")
        
        if self.new_line is None:
            self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
            self.new_line = False
            
        for i in range(len(lines)):
            line = lines[i]

            if i > 0:
                # add the date on any line which was empty before
                if self.new_line == True:
                    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                # cleaned any color, if it was not cleaned before
                if len(self.active_colors) > 0 and self.cleaned_color == False:
                    self.file.write("\x1b[0m")
                # start new line
                self.file.write("\n")
                self.new_line =  True
            
            # remove any clean color statement from the beginning of a line
            while len(line) >= 4:
                prefix = line[0:4]
                if prefix=="\x1b[0m":
                    #self.file.write(prefix)
                    line = line[4:]
                    self.active_colors = []
                else:
                    break
                        
            if line != "":
                if self.new_line == True:
                    # add the date to any new non empty line
                    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    # reinitialize registered colors
                    if len(self.active_colors) > 0:
                        for color in self.active_colors:
                            self.file.write(color)
                    self.new_line =  False

                # check if there are registered colors, is needed for the later 'cleanup' ending check
                had_colors = len(self.active_colors) > 0
                
                # find all color definitions
                colors = re.findall(r"(\x1b\[([0-9]+[;0-9]*)m)",line)
                for color in colors:
                    # handle clean color
                    if color[1] == "0":
                        self.active_colors = []
                    # else register color
                    else:
                        self.active_colors.append(color[0])
                        had_colors = True

                if len(line) >= 4:
                    # is the line ending with a cleanup?
                    if line[-4:] == "\x1b[0m":
                        # keep cleanup, because we had colors
                        if had_colors:
                            self.cleaned_color = True
                        # remove cleanup, because there was no used color
                        else:
                            line = line[0:-4]
                            self.cleaned_color = False
                    # no cleanup at the end
                    else:
                        self.cleaned_color = False

                self.file.write(u"{}".format(line))

            '''if i > 0:
                self.new_line =  True
                self.file.write("\n")
            
            if len(line) >= 4:
                prefix = line[0:4]
                if prefix=="\x1b[0m":
                    self.file.write(prefix)
                    line = line[4:]
                    self.active_colors = []
                        
            if line != "":
                if self.new_line == True:
                    if len(self.active_colors) > 0:
                        self.file.write("\x1b[0m")
                    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    if len(self.active_colors) > 0:
                        for color in self.active_colors:
                            self.file.write(color)
                    #self.file.write("{}|{} ".format(len(self.active_colors),datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    self.new_line =  False

                self.file.write(u"{}".format(line))

                colors = re.findall(r"(\x1b\[([0-9]+[;0-9]*)m)",line)
                for color in colors:
                    if color[1] == "0":
                        self.active_colors = []
                    else:
                        self.active_colors.append(color[0])'''
        
    def flush(self):
        self.file.flush()
