import re
import os
import logging
import threading
import subprocess
import select

from datetime import datetime

class LogFile:
    active_logs = {}
    lock = threading.Lock()

    def __init__(self, log_file, mode, callback=None, topic=None ):
        self.log_file = log_file
        self.mode = mode

        self.callback = callback
        self.topic = topic

        self.current_line =  None
        self.active_colors = []
        self.cleaned_color = False

        self.new_line =  None

        self.file = None

    @staticmethod
    def readFile(path):
        with LogFile.lock:
            if path in LogFile.active_logs:
                LogFile.active_logs[path].file.flush()
            with open(path, 'r') as f:
                return f.readlines()

    def __enter__(self):
        with LogFile.lock:
            self.file = open(self.log_file, self.mode)
            LogFile.active_logs[self.log_file] = self
        return self

    def __exit__(self, type, value, tb):
        with LogFile.lock:
            self._finishLine()
            del LogFile.active_logs[self.log_file]
        self.file.close()

    def _writeLine(self, line):
        with LogFile.lock:
            self.file.write(line)
        if self.callback is not None:
            self.callback(line, self.topic)

    def _finishLine(self):
        if self.current_line is None:
            return

        # cleaned any color, if it was not cleaned before
        if len(self.active_colors) > 0 and self.cleaned_color == False:
            self.current_line += "\x1b[0m"

        # start new line
        self.current_line += "\n"
        self._writeLine(self.current_line)
        self.current_line = None

    def writeRaw(self,text):
        self._finishLine()
        self._writeLine(text)

    def writeLine(self,text):
        self._finishLine()
        self.write(text)
        self._finishLine()

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

        #if self.new_line is None:
        #    self.file.write("{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3]))
        #    self.new_line = False

        for i in range(len(lines)):
            line = lines[i]

            if i > 0:
                # add the date on any line which was empty before
                if self.current_line is None:
                    self.current_line = "{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3])
                self._finishLine()

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
                if self.current_line is None:
                    # add the date to any new non empty line
                    self.current_line = "{} ".format(datetime.now().strftime("%H:%M:%S.%f")[:-3])
                    # reinitialize registered colors
                    if len(self.active_colors) > 0:
                        for color in self.active_colors:
                            self.current_line += color

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

                self.current_line += u"{}".format(line)

    def flush(self):
        self.file.flush()

    def getFile(self):
        return self.file

class LogFormatter:
    CODE_MAP = {
      '0': "</span>",
      '1': "<span style='font-weight:bold'>",
      '0;31': "<span style='color:#cc0000'>", # red
      '0;32': "<span style='color:green'>",
      '0;33': "<span style='color:#b2580c'>", # darkyellow
      '0;35': "<span style='color:magenta'>",
      '0;36': "<span style='color:cyan'>",
      '0;91': "<span style='color:red'>",
      '1;30': "<span style='color:gray'>",
      '1;31': "<span style='color:red'>",     # lightred
      '1;32': "<span style='color:#00cc00'>", # lightgreen
      '1;33': "<span style='color:yellow'>",
      '1;35': "<span style='color:plum'>"
    }

    def __init__(self, path):
        self.path = path
        self.content = []
        self.position = 0

    def __iter__(self):
        self.content = LogFile.readFile(self.path)
        return self

    def __next__(self):
        try:
            line = self.content[self.position]
            self.position += 1
            return LogFormatter.formatLine(line)
        except IndexError:
            raise StopIteration

    @staticmethod
    def formatLine(line):
        result = ['<div>']

        # format datetime
        if re.match("^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}.*$", line):
            result.append('<span style="color:#5a595c">{}</span>'.format(line[0:12]))
            line = line[12:]

        # force whitespaces
        line = re.sub("\s\s+", LogFormatter._whitespace,line)

        # convert color codes
        line = re.sub("\x1b\[([;0-9]+?)m", LogFormatter._color, line)

        # print final line
        result.append(line)

        result.append("</div>")

        return "".join(result)

    @staticmethod
    def _whitespace(m):
        return "<span style='white-space: pre;'>{}</span>".format(m.group(0))

    @staticmethod
    def _color(m):
        if m.group(1) in LogFormatter.CODE_MAP:
            return LogFormatter.CODE_MAP[m.group(1)]
        else:
            logging.error("Color code '{}' not found".format(m.group(1)))
            return m.group(0)

    '''@staticmethod
    def formatDuration(duration):
        days = math.floor(duration / 86400)
        duration -= days * 86400
        hours = floor(duration / 3600)
        duration -= hours * 3600
        minutes = floor(duration / 60)
        seconds = duration - minutes * 60

        hours = str(hours).zfill(2)
        minutes = str(minutes).zfill(2)
        seconds = str(seconds).zfill(2)

        return "{}:{}:{}".format(hours, minutes, seconds)'''

    '''@staticmethod
    def formatState(state):
        result = ['<span class="state {}"><span class="text">{}</span>'.format(state, state)]
        if state == "running":
            result.append('<span class="icon-dot"></span>')
        elif state == "success":
            result.append('<span class="icon-ok"></span>')
        elif state == "failed":
            result.append('<span class="icon-cancel"></span>')
        elif state == "crashed":
            result.append('<span class="icon-cancel"></span>')
        elif state == "retry":
            result.append('<span class="icon-ccw"></span>')
        elif state == "stopped":
            result.append('<span class="icon-block"></span>')
        result.append('</span>')

        return "".join(result)'''
