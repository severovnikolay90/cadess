# import sys
import logging
from asyncio import CancelledError
from os.path import dirname, exists, join

import servicemanager  # Simple setup and logging
import win32service  # Events
import win32serviceutil  # ServiceFramework and commandline helper
import socket
import win32event
import os, time, sys

from apisrv import ForkService, UvicornServer
from logger import formatter, logger


def get_installation_dir():
    def fallback():
        if getattr(sys, 'frozen', False):
            return dirname(sys.executable)
        raise FileNotFoundError("Не найдена директория с установленной службой CasCAdES")

    try: #Надо при инсталляции задать обязательно эту штуку в реестре
        import winreg as wr
        REG_PATH = r'SOFTWARE\CasCAdES'
        INST_DIR = 'Installation'

        try:
            regkey = wr.OpenKey(wr.HKEY_LOCAL_MACHINE, REG_PATH)
            (val, typ) = wr.QueryValueEx(regkey, INST_DIR)

            return val
        except FileNotFoundError:
            return fallback()

    except Exception as ex:
        logger.error(ex)
        return fallback()


SERVICE_WORKDIR = get_installation_dir()



def win_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback),
                 stack_info=True,
                 stacklevel=10)

sys.excepthook = win_excepthook


class CadesWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'CasCAdES'
    _svc_display_name_ = 'CasCAdES'
    _svc_description_ = 'API Service for CAdES sign documents'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(120)

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.uvisrv.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    # def SvcDoRun(self):
    #     """Start the service; does not return until stopped"""
    #     try:
    #         self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
    #         self.uvisrv = ForkService()
    #         self.ReportServiceStatus(win32service.SERVICE_RUNNING)
    #         # Run the service
    #         self.uvisrv.start()
    #         # while self.uvisrv.is_alive():
    #         #     self.uvisrv.join(10)
    #         win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
    #     except Exception as e:
    #         print(e)
    #         self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)
    def SvcDoRun(self):
        logger.debug('SvcDoRun')
        try:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_, ''))
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            self.uvisrv = UvicornServer()
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.uvisrv.run()
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        except Exception as e:
            logger.error(f"{e} (in SvcDoRun)", exc_info=e, stack_info=True, stacklevel=10)
            self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)


def init():
    os.chdir(get_installation_dir())

    file_h = logging.FileHandler(r'C:\cades.log')
    file2_h = logging.FileHandler(r'cades.log')
    file_h.setFormatter(formatter)
    file2_h.setFormatter(formatter)
    logger.addHandler(file_h)
    logger.addHandler(file2_h)

    logger.debug(sys.argv)
    logger.debug(sys.path)
    logger.debug(sys.executable)
    logger.debug(f"workdir = {os.getcwd()}")

    try:
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(CadesWinService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(CadesWinService)
    except CancelledError as e:
        logger.info("stop")
        exit(0)
    except KeyboardInterrupt as ki:
        logger.info("stop")
        exit(0)
    except Exception as e:
        logger.error(e, exc_info=e, stack_info=True)



if __name__ == '__main__':
    init()
