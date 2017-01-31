from urlparse import urlparse

from pyramid.settings import asbool

from twitcher.client import TwitcherService

from phoenix.db import mongodb
from phoenix.esgf.slcsclient import refresh_token

import logging
LOGGER = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings

    if asbool(settings.get('twitcher.ows_proxy_delegate', False)):
        config.include('twitcher.owsproxy')
    else:
        config.include('twitcher.rpcinterface')
        config.include('twitcher.owsproxy')
        config.include('twitcher.tweens')


def twitcher_service_factory(registry):
    settings = registry.settings
    service = TwitcherService(url=settings.get('twitcher.url'), verify=False)
    return service


def generate_access_token(registry, userid, valid_in_hours=1):
    service = twitcher_service_factory(registry)
    db = mongodb(registry)
    collection = db.users

    data = {}
    user = collection.find_one({'identifier': userid})
    esgf_token = user.get('esgf_token')
    if esgf_token:
        try:
            refresh_token(registry, token=esgf_token, userid=userid)
        except Exception as err:
            LOGGER.warn("Could not refresh token: {}".format(err.message))
        else:
            data['esgf_access_token'] = esgf_token.get('access_token', '')
            data['esgf_slcs_service_url'] = registry.settings.get('esgf_slcs_url', '')
    esgf_cert = user.get('credentials')
    if esgf_cert:
        data['esgf_credentials'] = esgf_cert

    # call to service
    token = service.generate_token(valid_in_hours, data)
    if userid and token:
        collection.update_one(
            {'identifier': userid},
            {'$set': {'twitcher_token': token, }})
    return token


def is_public(registry, name):
    srv = twitcher_service_factory(registry)
    service = srv.get_service_by_name(name)
    return service.get('public', False)
