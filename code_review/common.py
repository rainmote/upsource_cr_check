#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
import subprocess
import time
import pty
from threading import Timer

from log import debug, info, warning, error, fatal

##---------------------------------------------------------------------------------------
# # 如果不能用pip安装依赖包则使用egg
# # import python lib egg from third_party directory

# __strCurrentDir__ = os.path.abspath(os.path.dirname(__file__))
# deps = ['colored-1.3.93-py2.7.egg']
# fn = lambda x: sys.path.insert(0, os.path.join(__strCurrentDir__, 'third_party', x))
# map(fn, deps)
##---------------------------------------------------------------------------------------

from colored import fg, bg, attr

def colored_str(msg, color):
    return '{}{}{}'.format(fg(color), msg, attr('reset'))

def colored_print(msg, color):
    print(colored_str(msg, color))
    
class Common:
    def __init__(self):
        pass
    
    @staticmethod
    def get_env():
        length_limit = 100
        return dict(filter(lambda x:len(x[1]) < length_limit, os.environ.items()))
    
    @staticmethod
    def ch_dir(d):
        if not os.path.isdir(d):
            raise Exception('Not found dir: %s' % d)
        os.chdir(d)
        info('Change dir: %s' % d)
        
    @staticmethod
    def check_exists(d):
        if not os.path.exists(d):
            raise Exception('Not found: %s' % d)
        
    @staticmethod
    def popen_tty(cmd):
        master, slave = pty.openpty()
        proc = subprocess.Popen(cmd,
                                stdin=slave,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                close_fds=True,
                                preexec_fn=os.setsid)
        os.close(slave)
        return proc
    
    @staticmethod
    def popen(cmd):
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                close_fds=True,
                                preexec_fn=os.setsid)
        return proc
    
    @staticmethod
    def runcmd(cmd, timeout = 120, throw_exception= True, tty = False):
        info('Execute command [{}], timeout: {}'.format(cmd, timeout))
        proc = None
        if tty:
            proc = Common.popen_tty(cmd)
        else:
            proc = Common.popen(cmd)
            
        killProc = lambda p: os.killpg(p.pid, signal.SIGKILL)
        timer = Timer(timeout, killProc, [proc])
        stdout = None
        stderr = None
        start = time.time()
        try:
            timer.start()
            stdout, stderr = proc.communicate()
        finally:
            timer.cancel()
            cost = round(time.time() - start, 2)
            if isinstance(stdout, bytes):
                stdout = stdout.decode()
            info('CMD: {}\nRETRUN CODE: {}\nCOST: {}(s)\nSTDOUT:\n{}\n'.format(cmd, proc.returncode, cost, stdout))
            if stderr:
                warning('STDERR:\n%s\n' % stderr)
            if throw_exception and proc.returncode != 0:
                raise Exception('Run cmd [{}] failed\n{}\n{}'.format(cmd, stdout, stderr))
            return proc.returncode, stdout
        
    @staticmethod
    def runcmd_with_retry(cmd, timeout = 120, throw_exception = True, tty = False, retry_times = 5, retry_interval = 2):
        retry_throw_exception = False
        for i in range(retry_times):
            retcode, out = Common.runcmd(cmd, timeout, retry_throw_exception, tty)
            if retcode == 0:
                break
            
            warning('run cmd failed, cmd={}, retcode={}, out={}'.format(cmd, retcode, out))
            
            if i < retry_times - 1 and retry_interval > 0:
                time.sleep(retry_interval)
                
        if retcode != 0 and throw_exception:
            raise Exception('Run cmd [{}] failed!\n{}'.format(cmd, out))
        return retcode, out