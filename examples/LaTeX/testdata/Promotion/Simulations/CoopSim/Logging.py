# logging facilities

"""Module Logging.py contains classes to create a log and HTML report of
the simulation.
"""

import re, copy


H1, H2, H3, H1X, H2X, H3X = "<h3>", "<h4>", "<h5>", "</h3>", "</h4>", "</h5>"

class LogNotificationInterface:
    """Log notification interface to notify the application of status
    information or when the log has changed."""
    # old style class, because of some odd compatibility issues
    # with some (older) versions of python / wxWindows
    def updateLog(self, logStr):
        """Updates the changed log on the display."""
        raise NotImplementedError
    def logToStart(self):
        """Scrolls the log window back to the beginning."""
        raise NotImplementedError
    def statusBarHint(self, hint):
        """Display 'hint' on the status bar."""
        raise NotImplementedError


class HTMLLog(object):
    """A log logging class with facilities for creating HTML logs.
    The strings appended to the log may contain any HTML tags.

    Attributes:
        head, tail - lists of strings: Beginning and ending of the
            html page.
        body - list of lists of string: sections of lists of strings.
            One section for each entry point.
        entryPoints - dictionary of entry points.
    """
    def __init__(self):
        self.head = ["<html>\n<body>\n"]
        self.body = [[]]
        self.tail = ["</body>\n</html>\n"]
        self.entryPoints = {}

    def backup(self):
        """->all contents of the log, including entry points etc."""
        return copy.deepcopy((self.head, self.body,
                              self.tail, self.entryPoints))

    def replay(self, backup):
        """Replay a backed up log."""
        self.head, self.body, self.tail, self.entryPoints = \
            copy.deepcopy(backup)
        
    def clear(self):
        """Clears the log."""
        self.head = ["<html>\n<body>\n"]        
        self.body = [[]]

    def pageTitle(self, title):
        """Sets the HTML title of the page."""
        self.head = ["<html>\n<head>\n<title>" + title + \
                     "</title>\n</head>\n<body>\n"]
        
    def append(self, logStr):
        """Appends a single string to the log."""
        self.body[-1].append(logStr)
        
    def extend(self, strList):
        """Extends the log with a list of strings"""
        self.body[-1].extend(strList)

    def appendAt(self, entryPoint, logStr):
        """Inserts a string at the given entry point, moving the
        entry point to the end of the newly inserted part."""
        self.body[self.entryPoints[entryPoint]].append(logStr)

    def extendAt(self, entryPoint, logStr):
        """Inserts a list of strings at the given entry point, moving
        the entry point to the end of the newly inserted part."""        
        self.body[self.entryPoints[entryPoint]].extend(logStr)

    def entryPoint(self, name):
        """Defines a new entry point. Everything appended to the log
        will be appended after this (as well as all other) entry
        points."""
        self.entryPoints[name] = len(self.body)-1
        self.body.append([])
        
    def getHTMLPage(self):
        """Returns the whole log as HTML page, including image tags
        for the graphs."""
        # body = reduce(lambda x,y:x+y, self.body)
        body = []
        for item in self.body: body.extend(item)
        return "".join(self.head + body + self.tail)
    
    def getASCIIPage(self):
        """Returns the log as ascii string."""
        return re.sub("&nbsp;"," ",re.sub("<.*?>|\[.*?\]","",self.getHTMLPage()))

    
