#!/usr/bin/env python
#coding=utf-8
import logging

from flask import Flask, make_response, jsonify
from flask_restful import Resource, Api, reqparse, abort
from flask_httpauth import HTTPBasicAuth
import ipalib
from ipalib.errors import *
from krbcontext import krbcontext
import yaml


def load_conf(path):
    with open(path) as f:
        d = f.read()
        config = yaml.load(d)
    return config

try:
    conf = load_conf('/etc/ipa/api.yml')
    USER = conf['ipa']['user']
    DOMAIN = conf['ipa']['domain']
    KEYTAB = conf['ipa']['keytab']
    DEFAULT_SERVER = conf['ipa']['default_server']
    API_USER = conf['api']['user']
    API_PASS = conf['api']['password']
except:
    logging.error('parse config file /etc/ipa/api.yml error')
    exit(1)


app = Flask(__name__)
app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))
app.config.update(JSON_AS_ASCII=False)
api = Api(app)
webauth = HTTPBasicAuth()


@webauth.get_password
def get_password(username):
    if username == API_USER:
        return API_USER
    return None


@webauth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


parser = reqparse.RequestParser()
parser.add_argument('password', type=str, location='json')


def _init(server=DEFAULT_SERVER):
    '''
    ipa initialize.

    if default server fail, finalize method will automatically changing to server setting in
    /etc/ipa/default.conf.

    there is a compatible bug between ipa and salt.
    you must keep LANG envrion in saltmaster be en_US, otherwize will cause a salt-run failure.
    '''
    uri = 'https://{}.{}/ipa/xml'.format(server, DOMAIN)
    if ipalib.api.isdone('bootstrap') and ipalib.api.env.xmlrpc_uri != uri.decode('ascii'):
        reload(ipalib)
    api = ipalib.api
    with krbcontext(principal=USER, using_keytab=True, keytab_file=KEYTAB):
        if not api.isdone('bootstrap'):
            api.bootstrap(xmlrpc_uri=uri)
        if not api.isdone('finalize'):
            api.finalize()
        if not api.Backend.rpcclient.isconnected():
            api.Backend.rpcclient.connect()
    return api



class IpaUser(Resource):
    @webauth.login_required
    def post(self, username):
        try:
            api = _init()
        except:
            abort(500, error='ipa error, can not initialize api endpoint')
        username = username.decode('ascii')
        args = parser.parse_args()
        try:
            password = args['password'].decode('ascii')
        except:
            abort(400, error='there is no password')
        try:
            api.Command.user_add(username,
                                 givenname=username,
                                 sn=username,
                                 cn=username,
                                 krbprincipalexpiration=u'20581224151641Z',
                                 userpassword=password)
            return {'message': 'add a new user {}'.format(username)}
        except DuplicateEntry:
            try:
                api.Command.user_mod(username, userpassword=password, rights=True)
                return {'message': 'reset password for {}'.format(username)}
            except:
                abort(500, error='ipa reset password fail')
        except:
            abort(500, error='ipa add user fail')

    @webauth.login_required
    def delete(self, username):
        try:
            api = _init()
        except:
            abort(500, error='ipa error, can not initialize api endpoint')
        username = username.decode('ascii')
        try:
            api.Command.user_del(username)
        except NotFound:
            abort(403, error='user {} not in ipa'.format(username))
        except Exception as e:
            abort(500, error=str(e))

    @webauth.login_required
    def get(self, username):
        try:
            api = _init()
        except:
            abort(500, error='ipa error, can not initialize api endpoint')
        username = username.decode('ascii')
        try:
            ret = api.Command.user_show(username, all=True)
            return jsonify(ret)
        except NotFound:
            abort(403, error='user {} not in ipa'.format(username))
        except Exception as e:
            abort(500, error=str(e))


api.add_resource(IpaUser, '/user/<string:username>')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
