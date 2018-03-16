from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.compat import escape

from phoenix.twitcherclient import generate_access_token
from phoenix.esgf.slcsclient import ESGFSLCSClient


class Actions(object):
    def __init__(self, request):
        self.request = request
        self.session = request.session
        # settings = request.registry.settings
        self.collection = self.request.db.users
        self.userid = self.request.matchdict.get('userid', authenticated_userid(self.request))

    @view_config(route_name='update_esgf_certs', permission='edit')
    def update_esgf_certs(self):
        client = ESGFSLCSClient(self.request)
        if client.get_token():
            try:
                client.get_certificate()
            except Exception as err:
                self.session.flash('Could not update certificate: {}'.format(escape(err.message)), queue="danger")
            else:
                self.session.flash('ESGF certificate was updated.', queue="success")
            return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='esgf_certs'))
        elif False:  # TODO: update slcs token ... slcs does not work yet
            auth_url = client.authorize()
            return HTTPFound(location=auth_url)
        else:
            callback = self.request.route_path('profile', userid=self.userid, tab='esgf_certs')
            return HTTPFound(location=self.request.route_path('esgflogon', _query=[('callback', callback)]))

    @view_config(route_name='forget_esgf_certs', permission='edit')
    def forget_esgf_certs(self):
        user = self.collection.find_one({'identifier': self.userid})
        user['credentials'] = None
        user['cert_expires'] = None
        self.collection.update({'identifier': self.userid}, user)
        self.session.flash("ESGF credentials removed.", queue='info')
        return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='esgf_certs'))

    @view_config(route_name='generate_twitcher_token', permission='submit')
    def generate_twitcher_token(self):
        try:
            generate_access_token(self.request.registry, userid=self.userid)
        except Exception as err:
            self.session.flash('Could not refresh token: {}'.format(escape(err.message)), queue="danger")
        else:
            self.session.flash('Twitcher token was updated.', queue="success")
        return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='twitcher'))

    @view_config(route_name='generate_esgf_slcs_token', permission='submit')
    def generate_esgf_slcs_token(self):
        """
        Update ESGF slcs token.
        """
        client = ESGFSLCSClient(self.request)
        if client.get_token():
            try:
                client.refresh_token()
            except Exception as err:
                self.session.flash('Could not refresh token: {}'.format(escape(err.message)), queue="danger")
            else:
                self.session.flash('ESGF token was updated.', queue="success")
            return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='esgf_slcs'))
        else:
            try:
                auth_url = client.authorize()
            except Exception as err:
                self.session.flash('Could not retrieve token: {}'.format(escape(err.message)), queue="danger")
                return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='esgf_slcs'))
            else:
                return HTTPFound(location=auth_url)

    @view_config(route_name='forget_esgf_slcs_token', permission='submit')
    def forget_esgf_slcs_token(self):
        """
        Forget ESGF slcs token.
        """
        client = ESGFSLCSClient(self.request)
        client.delete_token()
        self.session.flash("ESGF token removed.", queue='info')
        return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='esgf_slcs'))

    @view_config(route_name='esgf_oauth_callback', permission='submit')
    def esgf_oauth_callback(self):
        """
        Convert an authorisation grant into an access token.
        """
        client = ESGFSLCSClient(self.request)
        if client.callback():
            # Redirect to the token view
            return HTTPFound(location=self.request.route_path('profile', userid=self.userid, tab='esgf_slcs'))
        else:
            # If we have not yet entered the OAuth flow, redirect to the start
            return HTTPFound(location=self.request.route_path('generate_esgf_slcs_token'))

    @view_config(route_name='delete_user', permission='admin')
    def delete_user(self):
        if self.userid:
            self.collection.remove(dict(identifier=self.userid))
            self.session.flash('User removed', queue="info")
        return HTTPFound(location=self.request.route_path('people'))


def includeme(config):
    """ Pyramid includeme hook.
    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """
    config.add_route('update_esgf_certs', 'people/update_esgf_certs')
    config.add_route('forget_esgf_certs', 'people/forget_esgf_certs')
    config.add_route('generate_twitcher_token', 'people/gentoken')
    config.add_route('generate_esgf_slcs_token', 'people/generate_esgf_token')
    config.add_route('forget_esgf_slcs_token', 'people/forget_esgf_token')
    config.add_route('esgf_oauth_callback', 'account/oauth/esgf/callback')
    config.add_route('delete_user', 'people/delete/{userid}')
