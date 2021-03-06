from pyramid.settings import asbool
from pyramid.events import NewRequest

from phoenix.twitcherclient import twitcher_service_factory

from owslib.wps import WebProcessingService

import logging
logger = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings

    if asbool(settings.get('phoenix.wizard', 'false')):
        config.include('phoenix.twitcherclient')

        config.include('phoenix.wizard.views.start')
        config.include('phoenix.wizard.views.wps')
        config.include('phoenix.wizard.views.wpsprocess')
        config.include('phoenix.wizard.views.literalinputs')
        config.include('phoenix.wizard.views.complexinputs')
        config.include('phoenix.wizard.views.source')
        config.include('phoenix.wizard.views.esgfsearch')
        config.include('phoenix.wizard.views.threddsservice')
        config.include('phoenix.wizard.views.solrsearch')
        config.include('phoenix.wizard.views.done')

        # add malleefowl wps
        def get_wps(request):
            settings = request.registry.settings
            if 'wps' not in settings:
                logger.debug('register malleefowl wps service')
                try:
                    service_name = 'malleefowl'
                    registry = twitcher_service_factory(request.registry)
                    logger.debug("register: name=%s, url=%s", service_name, settings['wps.url'])
                    registry.register_service(url=settings['wps.url'], data={'name': service_name}, overwrite=True)
                    settings['wps'] = WebProcessingService(
                        url=request.route_url('owsproxy', service_name=service_name),
                        skip_caps=True, verify=False)
                    logger.debug('malleefowl proxy url: %s', settings['wps'].url)
                except:
                    logger.exception('Could not connect malleefowl wps %s', settings['wps.url'])
            return settings.get('wps')
        config.add_request_method(get_wps, 'wps', reify=True)

    # check if wizard is activated
    def wizard_activated(request):
        return asbool(settings.get('phoenix.wizard', 'false'))
    config.add_request_method(wizard_activated, reify=True)
