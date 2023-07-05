import threading
from datetime import datetime
from getpass import getpass

class LoggerCache:
    pass

class Log:
    _loggerCache = {}
    _consoleLock = threading.Lock()

    def __new__(cls, file_path, console=True):
        ident = "LoggerIdent" + file_path.replace("/", "").replace("\\", "").replace(".", "")
        if hasattr(LoggerCache, ident):
            return getattr(LoggerCache, ident)

        obj = super().__new__(cls)
        obj.file_path = file_path
        obj.consoleEnable = console
        
        obj.EMERGENCY = 0
        obj.ALERT = 1
        obj.CRITICAL = 2
        obj.ERROR = 3
        obj.WARNING = 4
        obj.NOTICE = 5
        obj.INFO = 6
        obj.DEBUG = 7
        obj.ECHO = 8
        obj.SECURITY = 9
        obj.TRACE = 10

        obj.level_str = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR", "WARNING", "NOTICE", "INFO", "DEBUG", "ECHO", "SECURITY", "TRACEBACK"]
        obj.dtFormat = "%m-%d-%Y %H:%M:%S"
        obj.logFormat = "[{date_time}] [{log_level}]: {message}"

        obj._queueLock = threading.Lock()

        obj._logQueue = []
        obj._logCondition = threading.Condition()
        setattr(LoggerCache, ident, obj)

        obj._initLogProcessor()

        return obj

    def print(self, *args, **kwargs):
        with Log._consoleLock:
            print(*args, **kwargs)

    def input(self, prompt):
        with Log._consoleLock:
            inp = input(prompt)
        return inp

    def getpass(self, prompt):
        with Log._consoleLock:
            inp = getpass(prompt)
        return inp

    def log(self, log_level, message): #Note to self: do sum fuckin threading magic to speed this up dummy
        string = self.logFormat.format(
            date_time=datetime.now().strftime(self.dtFormat),
            log_level=self.level_str[log_level],
            message=message
        )
        with self._logCondition:
            self._logQueue.append(string)
            self._logCondition.notify_all()

    def _initLogProcessor(self):
        self._processor = threading.Thread(target=self._processLogEntries, daemon=True)
        self._processor.start()

    def _processLogEntries(self):
        with self._logCondition:

            while True:
                while not len(self._logQueue):
                    self._logCondition.wait()

                string = self._logQueue.pop(0)

                with open(self.file_path, 'a+') as file:
                    file.write(string+"\n")

                if self.consoleEnable:
                    self.print(string)
