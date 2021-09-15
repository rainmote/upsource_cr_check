#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import requests
import json
import time
import pprint
from requests.auth import HTTPBasicAuth

import urllib3
urllib3.disable_warnings()

from log import debug, info, warning, error, fatal

''''
https://<your_upsource_domain>/~api_doc/reference/Service.html#messages.UpsourceRPC
'''

def wrapper(func):
    def f_(self, *args, **kw):
        return self.request(func.__name__, *args, **kw)
    return f_

class Upsource:
    ENDPOINT = 'https://<your_upsource_domain>'
    
    REQUEST_MAP = {
        'getProjectInfo': ['projectId'],
        'getCodeReviewPatterns': [],
        'getRevisionsList': ['projectId', 'limit', 'skip = 0', 'requestGraph = False'],
        'getRevisionsListFiltered': ['projectId', 'query', 'limit', 'skip = 0', 'requestGraph = False'],
        'getRevisionInfo': ['projectId', 'revisionId'],
        'getBranchInfo': ['projectId', 'branch'],
        'getBranchGraph': ['projectId', 'branch'],
        'getBranches': ['projectId', 'query', 'limit', 'sortBy = "updated"'],
        'findCommits': ['commits', 'requestChanges = False', 'limit = 10'],
        'getReviews': ['limit', 'query = "*"', 'sortBy = "updated"', 'projectId', 'skip = 0'],
    }
    
    def __init__(self, user, passwd, retry_times = 3):
        self.__auth = HTTPBasicAuth(user, passwd)
        self.retry_times = retry_times
        
        # dynamic gen class function from REQUEST_MAP
        for k, v in self.REQUEST_MAP.items():
            fn_str = '''def {}(self, {}): m = locals(); m.pop('self'); return self.request(m);'''.format(k, ', '.join(v))
            info('class: {}, gen function: {}'.format(self.__class__.__name__, fn_str))
            exec(fn_str)
            setattr(Upsource, k, locals().get(k))
            
    def _request(self, rpc_name, data):
        suffix = '/~rpc/{}'.format(rpc_name)
        url = self.ENDPOINT + re.sub('/+', '/', suffix)
        
        headers = {'Content-Type': 'applition/json; charset=utf-8'}
        proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
        info('{}, request: {}'.format(rpc_name, data))
        
        retry = self.retry_times
        while retry > 0:
            retry -= 1
            resp = None
            try:
                resp = requests.post(url, data=json.dumps(data), auth=self.__auth, headers=headers, verify=False)
                if resp and resp.status_code == 200:
                    return json.loads(resp.text)['result']
                raise Exception('request failed')
            except Exception as e:
                error('request upsource failed! rpc_name: {}, request: {}, resp: {}, error: {}'.format(rpc_name, data, resp.text, str(e)))
            time.sleep(1)
            
    def request(self, data):
        rpc_name = sys._getframe(1).f_code.co_name
        resp = self._request(rpc_name, data)
        info(pprint.pformat(resp))
        return resp

if __name__ == '__main__':
    up = Upsource('admin', 'password')
    print(up.getProjectInfo('projectName'))