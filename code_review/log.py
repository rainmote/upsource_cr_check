#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import logging.handlers

def pretty_format(msg, pretty, extra = ''):
    if pretty:
        return extra + '\n' + json.dumps(msg, indent=4, sort_keys=True)
    return str(msg)

def get_log_header(msg):
    filename = sys._getframe(2).f_code.co_filename
    filename = filename[(filename.rfind('/') + 1):]
    if not isinstance(msg, str):
        msg = str(msg)
    return '[%s:%s]' % (filename, str(sys._getframe(2).f_lineno)) + msg

def logger_fn(level):
    def fn(msg, **kw):
        if 'pretty' in kw:
            msg = pretty_format(msg, kw['pretty'])
        msg = get_log_header(msg)
        getattr(Logger.GetInstace(), level.__name__)(msg)
        return msg
    return fn

@logger_fn
def debug(msg, pretty = False):
    pass

@logger_fn
def info(msg, pretty = False):
    pass

@logger_fn
def warning(msg, pretty = False):
    pass

@logger_fn
def error(msg, pretty = False):
    pass

@logger_fn
def fatal(msg, pretty = False):
    pass

class Logger:
    OBJ = None
    
    @staticmethod
    def GetInstance():
        if not Logger.OBJ:
            Logger.OBJ = Logger.create_logger('.', 'default.log')
        return Logger.OBJ
    
    @staticmethod
    def GetLogger(logFilePath, logFileMaxLength, backupCount, level):
        logFileHandler = logging.handlers.RotatingFileHandler(logFilePath, maxBytes=logFileMaxLength, backupCount=backupCount)
        fmt = '%(asctime)s %(levelname)s %(message)s'
        logItemFormatter = logging.Formatter(fmt)
        logFileHandler.setFormatter(logItemFormatter)
        
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logItemFormatter)
        
        logger = logging.getLogger(logFilePath)
        logger.addHandler(logFileHandler)
        logger.addHandler(consoleHandler)
        logger.setLevel(level)
        return logger
    
    @staticmethod
    def create_logger(path, name):
        if Logger.OBJ:
            return Logger.OBJ
        
        if not os.path.isdir(path):
            os.makedirs(path)
            
        Logger.OBJ = Logger.GetLogger(os.path.join(path, name), 512*1024, 50, logging.INFO)
        return Logger.OBJ        