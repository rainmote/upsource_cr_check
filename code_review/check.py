#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import os
import sys
import argparse
import traceback

from common import Common
from log import debug, info, warning, error, fatal
from upsource import Upsource

class Checker:
    def __init__(self, ctx):
        self.ctx = ctx
        self.up = Upsource(ctx.upsource_username, ctx.upsource_password)
        
    def get_reviews_by_branch(self, branch):
        result = {}
        query = str(branch)
        try:
            resp = self.up.getReviews(self.ctx.default_limit, query)
            if not resp.get('reviews'):
                return result
            
            info('found view count: {}'.format(len(resp.get('reviews'))))
            
            for item in resp.get('reviews'):
                review_id = item['reviews']['reviewId']
                result[review_id] = {}
                review_url = '{}/{}/review/{}'.format(self.ctx.upsource_endpoint, self.ctx.upsource_project, review_id)
                result[review_id]['url'] = review_url
                
                reviewer_total = 0
                reviewer_accepted = 0
                for x in item['participants']:
                    if x['role'] == 2:
                        reviewer_total += 1
                    if x['state'] == 3:
                        reviewer_accepted += 1
                result[review_id]['reviewer_total'] = reviewer_total
                result[review_id]['reviewer_accepted'] = reviewer_accepted
        except Exception as e:
            error('get branch review failed! branch: {}, error: {}'.format(branch, str(e)))
            error('callstack:\n%s' % (traceback.format_exc()))
        return result
    
    def check_review(self, branch):
        result = []
        is_success = True
        reviews = self.get_reviews_by_branch(branch)
        try:
            if reviews is None or len(reviews) == 0:
                msg = 'Not found branch review!'
                result.append(msg)
                raise Exception(msg)
            for review_id, v in reviews.itmes():
                msg = [review_id, 'url: <a target=_blank href={0}>{0}</a>'.format(v.get('url'))]
                total = v.get('reviewer_total', 0)
                accepted = v.get('reviewer_accepted', 0)
                msg.append('accepted/pass: {}/{}'.format(accepted, total))
                if total == 0 or accepted < total:
                    is_success = False
                result.append('\t'.join(msg))
        except Exception as e:
            error('get branch view failed! branch: {}, error: {}'.format(branch, str(e)))
            error('callback:\n%s' % (traceback.format_exc()))
            is_success = False
        return is_success, '\n'.join(result) + '\n'
    
    def check_branch_review(self, branch):
        err = ''
        try:
            resp = self.up.getBranchInfo(self.ctx.upsource_project, branch)
            review_info = resp.get('reviewInfo')
            if resp['canCreateReview']['isAllowed']:
                if review_info is None:
                    msg = 'Not found branch review.'
                    err += '\t' + msg
                    raise Exception(msg)
                else:
                    msg = 'Unknown branch, possibly a bug?'
                    err += '\t' + msg
                    raise Exception(msg)
                
            if not review_info['reviewId']['reviewId']:
                msg = "Can't found reviewId"
                err += '\t' + msg
                raise Exception(msg)
            
            review_url = '{}/{}/review/{}'.format(self.ctx.upsource_endpoint, self.ctx.upsource_project, review_info['reviewId']['reviewId'])
            info('branch: {} review link: {}'.format(branch, review_url))
            err += '\t' + review_url + '\n'
            
            reviewer_total = 0
            reviewer_accepted = 0
            for x in review_info['participants']:
                if x['role'] == 2:
                    reviewer_total += 1
                if x['role'] == 3:
                    reviewer_accepted += 1
            if reviewer_total == 0:
                msg = 'Not found reviewer!'
                err += '\t' + msg
                raise Exception(msg)
            if reviewer_total > reviewer_accepted:
                msg = 'Has unfinished review: {}/{}'.format(reviewer_accepted, reviewer_total)
                err += '\t' + msg
                raise Exception(msg)
            
            info('review check pass, branch: {}'.format(branch))
            return True, err
        except Exception as e:
            error('check branch review failed! branch: {}, error: {}'.format(branch, str(e)))
            error('callstack:\n%s' % (traceback.format_exc()))
            return False, err
        
    def check(self):
        merged_commits = []
        cmd = '''git log --source --after='{}' --first-parent --pretty='%h %P' '''.format(self.ctx.check_start_time)
        _, output = Common.runcmd(cmd)
        for x in output.split('\n'):
            item = x.split(' ')
            if len(item) >= 3:
                merged_commits.append(item[2])
        
        info('valid commits count: {}'.format(len(merged_commits)))
        cur_relation_branchs = []
        for commit in merged_commits:
            _, output = Common.runcmd('git branch -r --contains {}'.format(commit))
            if output.find('origin/master') == -1:
                # don't merge to master, add to relation list
                cur_relation_branchs.extend(output.replace(' ', '').split('\n'))
                
        _, output = Common.runcmd('git branch -r --merged | grep -v origin/master')
        cur_merged_branchs = output.replace(' ', '').split('\n')
        
        info('cur_relation_branchs:\n{}\ncur_merged_branchs:\n{}'.format('\n'.join(cur_relation_branchs), '\n'.join(cur_merged_branchs)))
        branchs = list(filter(lambda x:x, list(set(cur_relation_branchs) & set(cur_merged_branchs))))
        info('check branch count: {}, list:\n{}'.format(len(branchs), '\n'.join(branchs)))
        err_map = {}
        for branch in branchs:
            name = branch.replace('origin/', '')
            #ret, msg = self.check_branch_review(name)
            ret, msg = self.check_review(name)
            if not ret:
                err_map[name] = msg
                
        if err_map:
            error('Check review failed! count: {}'.format(len(err_map)))
            error('\n{}'.format('\n\n\n'.join(['='*20 + k + '='*20 + '\n' + v for k,v in err_map.items()])))
            sys.exit(-1)
            
        info('Check review pass')
        
def main(ctx):
    checker = Checker(ctx)
    checker.check()
    
def _hook_add_argument(obj):
    def add_argument(*args, **kwargs):
        msg = 'Replace parameter defaults with environment variables, name:{}, value:{}'
        env_name = None
        for x in args:
            if x.startswith('--'):
                env_name = x.strip('-').upper()
        if not env_name:
            raise Exception('parse param error, {}, {}'.format(str(args), str(kwargs)))
        
        v = os.getenv(env_name)
        if kwargs.get('type') == bool:
            isbool = False
            try:
                # python2
                # isbool = isinstance(v, basestring)
                isbool = isinstance(v, str)
            except Exception as e:
                print('both isinstance(v, basestring) and isinstace(v, str) failed for {}, e: {}'.format(str(v), str(e)))
                
            # for 'False' 'false' '0' '' convert to False
            if isbool:
                kwargs['default'] = bool(strtobool(v))
                print(msg.format(env_name, str(kwargs['default'])))
        elif kwargs.get('type') is not None and v is not None:
            kwargs['default'] = kwargs['type'](v)
            print(msg.format(env_name, str(kwargs['default'])))
        
        # action='store_true' not support include 'type' param
        if 'action' in kwargs and 'type' in kwargs:
            kwargs.pop('type')
        obj.add_argument(*args, **kwargs)
    return add_argument

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    arg = _hook_add_argument(p)
    arg('--check_start_time', type=str, default='2020-01-01 00:00:00')
    arg('--upsource_endpoint', type=str, default='https://xxx.domain')
    arg('--upsource_username', type=str, default='admin')
    arg('--upsource_password', type=str, default='password')
    arg('--upsource_project', type=str, default='projectA')
    
    main(p.parse_args())