import os
import datetime

from pyramid.view import (
    view_config,
    view_defaults,
    forbidden_view_config,
    notfound_view_config
    )
from pyramid.httpexceptions import HTTPException, HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.renderers import render
from pyramid.security import remember, forget, authenticated_userid
from pyramid.events import subscriber, BeforeRender
from deform import Form, Button
from deform import ValidationFailure
from authomatic import Authomatic
from authomatic.adapters import WebObAdapter

from owslib.wps import (
    WebProcessingService,
    WPSExecution,
    )

import models
from .security import is_valid_user

import logging
logger = logging.getLogger(__name__)

import config_public as config
authomatic = Authomatic(config=config.config,
                        secret=config.SECRET,
                        report_errors=True,
                        logging_level=logging.DEBUG)

@notfound_view_config(renderer='templates/404.pt')
def notfound(request):
    """This special view just renders a custom 404 page. We do this
    so that the 404 page fits nicely into our global layout.
    """
    return {}

@forbidden_view_config(renderer='templates/forbidden.pt')
def forbidden(request):
    request.response.status = 403
    return dict(message=None)

@subscriber(BeforeRender)
def add_global(event):
    event['message_type'] = 'alert-info'
    event['message'] = ''

@view_config(context=Exception)
def unknown_failure(request, exc):
    #import traceback
    logger.exception('unknown failure')
    #msg = exc.args[0] if exc.args else ""
    #response =  Response('Ooops, something went wrong: %s' % (traceback.format_exc()))
    response =  Response('Ooops, something went wrong. Check the log files.')
    response.status_int = 500
    return response

class MyView(object):
    def __init__(self, request, title, description=''):
        self.request = request
        self.session = self.request.session
        self.title = title
        self.description = description

@view_defaults(permission='view', layout='default')
class PhoenixViews:
    def __init__(self, request):
        self.request = request
        self.userdb = models.User(self.request)

    @view_config(route_name='signin', renderer='templates/signin.pt')
    def signin(self):
        return dict()

    @view_config(route_name='logout', permission='edit')
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = self.request.route_url('home'), headers = headers)

    @view_config(route_name='register', renderer='templates/register.pt')
    def register(self):
        return dict(email=None)

    @view_config(route_name='login_local')
    def login_local(self):
        """local login for admin and demo user"""
        
        # TODO: need some work work on local accounts
        if (True):
            email = "admin@malleefowl.org"
            self.userdb.update(user_id=email)

            if is_valid_user(self.request, email):
                self.request.response.text = render('phoenix:templates/openid_success.pt',
                                               {'result': email},
                                               request=self.request)
                # Add the headers required to remember the user to the response
                self.request.response.headers.extend(remember(self.request, email))
            else:
                self.request.response.text = render('phoenix:templates/register.pt',
                                               {'email': email}, request=self.request)
        else:
            self.request.response.text = render('phoenix:templates/forbidden.pt',
                                           {'message': 'Wrong Password'},
                                           request=self.request)

        return self.request.response

    @view_config(route_name='login_openid')
    def login_openid(self):
        """authomatic openid login"""
        # Get the internal provider name URL variable.
        provider_name = self.request.matchdict.get('provider_name', 'openid')

        logger.debug('provider_name: %s', provider_name)

        # Start the login procedure.
        response = Response()
        #response = request.response
        result = authomatic.login(WebObAdapter(self.request, response), provider_name)

        logger.debug('authomatic login result: %s', result)

        if result:
            if result.error:
                # Login procedure finished with an error.
                #request.session.flash('Sorry, login failed: %s' % (result.error.message))
                logger.error('openid login failed: %s', result.error.message)
                #response.write(u'<h2>Login failed: {}</h2>'.format(result.error.message))
                response.text = render('phoenix:templates/forbidden.pt',
                                       {'message': result.error.message}, request=self.request)
            elif result.user:
                # Hooray, we have the user!
                logger.debug("user=%s, id=%s, email=%s, credentials=%s",
                          result.user.name, result.user.id, result.user.email, result.user.credentials)
                logger.debug("provider=%s", result.provider.name )
                logger.debug("response headers=%s", response.headers.keys())
                #logger.debug("response cookie=%s", response.headers['Set-Cookie'])

                if is_valid_user(self.request, result.user.email):
                    logger.info("openid login successful for user %s", result.user.email)
                    try:
                        self.userdb.update(user_id=result.user.email,
                                      openid=result.user.id,
                                      activated=True)
                    except Exception, e:
                        logger.exception("update user failed")
                    response.text = render('phoenix:templates/openid_success.pt',
                                           {'result': result},
                                           request=self.request)
                    # Add the headers required to remember the user to the response
                    response.headers.extend(remember(self.request, result.user.email))
                else:
                    logger.info("openid login: user %s is not registered", result.user.email)
                    self.userdb.update(user_id=result.user.email,
                                  openid=result.user.id,
                                  activated=False)
                    response.text = render('phoenix:templates/register.pt',
                                           {'email': result.user.email}, request=self.request)
        #logger.debug('response: %s', response)

        return response

    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        lm = self.request.layout_manager
        lm.layout.add_heading('info')
        return dict()

@view_defaults(permission='view', layout='default')
class Dashboard(MyView):
    def __init__(self, request):
        super(Dashboard, self).__init__(request, 'Dashboard')

    @view_config(route_name='dashboard', renderer='templates/dashboard.pt')
    def view(self):
        lm = self.request.layout_manager
        lm.layout.add_heading('dashboard_users')

        return dict(
            title=self.title,
            description=self.description,
            )

@view_defaults(permission='edit', layout='default')
class Processes(MyView):
    def __init__(self, request):
        super(Processes, self).__init__(request, 'WPS Processes')

        self.wps = None
        if 'wps.url' in self.session:
            try:
                self.wps = WebProcessingService(url=self.session['wps.url'])
                self.description = self.wps.identification.title
            except:
                msg = "Could not connect to wps"
                logger.exception(msg)
                self.session.flash(msg, queue='error')

    def sort_order(self):
        """Determine what the current sort parameters are.
        """
        order = self.request.GET.get('order_col', 'identifier')
        order_dir = self.request.GET.get('order_dir', 'asc')
        ## if order == 'due_date':
        ##     # handle sorting of NULL values so they are always at the end
        ##     order = 'CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date'
        ## if order == 'task':
        ##     # Sort ignoring case
        ##     order += ' COLLATE NOCASE'
        order_dir = 1 if order_dir == 'asc' else -1
        return dict(order=order, order_dir=order_dir)
    
    def generate_form(self, formid='deform'):
        from .schema import ChooseWPSSchema
        schema = ChooseWPSSchema().bind(wps_list = models.get_wps_list(self.request))
        return Form(
            schema,
            buttons=('submit',),
            formid=formid
            )
    def process_form(self, form):
        controls = self.request.POST.items()
        try:
            captured = form.validate(controls)
            url = captured.get('url', '')
            session = self.request.session
            session['wps.url'] = url
            session.changed()
        except ValidationFailure, e:
            logger.exception('validation of process view failed.')
            return dict(title=self.title, description=self.description, form=e.render())
        return HTTPFound(location=self.request.route_url('processes'))

    @view_config(route_name='processes', renderer='templates/processes.pt')
    def view(self):
        form = self.generate_form()
        if 'submit' in self.request.POST:
            return self.process_form(form)

        items = []
        if self.wps is not None:
            for process in self.wps.processes:
                items.append(dict(title=process.title,
                                  identifier=process.identifier,
                                  abstract = process.abstract,
                                  version = process.processVersion))

        # sort items
        order = self.sort_order()
        import operator
        items.sort(key=operator.itemgetter(order['order']), reverse=order['order_dir']==-1)

        from .grid import ProcessesGrid
        grid = ProcessesGrid(
                self.request,
                items,
                ['title', 'abstract', 'action'],
            )
        return dict(
            title=self.title,
            description=self.description,
            grid=grid,
            items=items,
            form=form.render())

@view_defaults(permission='edit', layout='default')
class Execute(MyView):
    def __init__(self, request):
        super(Execute, self).__init__(request, 'Execute')
        
        self.db = self.request.db
       
        self.identifier = self.request.params.get('identifier', None)
        self.wps = self.request.wps
        if 'wps.url' in self.session:
            url = self.session['wps.url']
            self.wps = WebProcessingService(url)
        self.process = self.wps.describeprocess(self.identifier)
        self.description = self.process.title

    def generate_form(self, formid='deform'):
        from .wps import WPSSchema
        # TODO: should be WPSSchema.bind() ...
        schema = WPSSchema(info=True, process = self.process)
        return Form(
            schema,
            buttons=('submit',),
            formid=formid,
            )
    
    def process_form(self, form):
        controls = self.request.POST.items()
        try:
            appstruct = form.validate(controls)

            from .helpers import execute_wps
            execution = execute_wps(self.wps, self.identifier, appstruct)

            models.add_job(
                request = self.request,
                wps_url = execution.serviceInstance,
                status_location = execution.statusLocation,
                notes = appstruct.get('info_notes', ''),
                tags = appstruct.get('info_tags', ''))
        except ValidationFailure, e:
            logger.exception('validation of exectue view failed.')
            return dict(title=self.title, description=self.description, form = e.render())
        return HTTPFound(location=self.request.route_url('jobs'))

    @view_config(route_name='execute', renderer='templates/execute.pt')
    def execute_view(self):
        form = self.generate_form()
        if 'submit' in self.request.POST:
            return self.process_form(form)
        return dict(
            title=self.title,
            description=self.description,
            form=form.render())
    
@view_defaults(permission='edit', layout='default')
class Jobs(MyView):
    def __init__(self, request):
        super(Jobs, self).__init__(request, 'My Jobs')
        self.db = self.request.db 

    def sort_order(self):
        """Determine what the current sort parameters are.
        """
        order = self.request.GET.get('order_col', 'start_time')
        order_dir = self.request.GET.get('order_dir', 'desc')
        ## if order == 'due_date':
        ##     # handle sorting of NULL values so they are always at the end
        ##     order = 'CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date'
        ## if order == 'task':
        ##     # Sort ignoring case
        ##     order += ' COLLATE NOCASE'
        order_dir = 1 if order_dir == 'asc' else -1
        return dict(order=order, order_dir=order_dir)

    @view_config(renderer='json', name='update.jobs')
    def update_jobs(self):
        order = self.sort_order()
        key=order.get('order')
        direction=order.get('order_dir')

        from owslib.wps import WPSExecution

        items = []
        for job in self.db.jobs.find({'userid': authenticated_userid(self.request)}).sort(key, direction):
            try:
                logger.debug("update job: %s", job['identifier'])
                item = dict(
                    identifier = job['identifier'],
                    status_location = job['status_location'])
                
                execution = WPSExecution(url = job['wps_url'])
                execution.checkStatus(url = job['status_location'], sleepSecs=0)
                item['status'] = job['status'] = execution.getStatus()
                item['status_message'] = job['status_message'] = execution.statusMessage
                job['is_complete'] = execution.isComplete()
                job['is_succeded'] = execution.isSucceded() 
                if execution.isSucceded():
                    item['progress'] = job['progress'] = 100
                else:
                    item['progress'] = job['progress'] = execution.percentCompleted
                # update db
                self.db.jobs.update({'identifier': job['identifier']}, job)
            except:
                logger.exception("could not update job %s", job.get('identifier'))
            else:
                items.append( item )
        return items

    @view_config(renderer='json', name='deleteall.job')
    def delete_all(self):
        self.db.jobs.remove({'userid': authenticated_userid(self.request)})
        return {}

    @view_config(renderer='json', name='delete.job')
    def delete(self):
        jobid = self.request.params.get('jobid', None)
        if jobid is not None:
            self.db.jobs.remove({'identifier': jobid})

        return {}
    
    @view_config(route_name='jobs', renderer='templates/jobs.pt')
    def view(self):
        items = self.update_jobs()
        
        from .grid import JobsGrid
        grid = JobsGrid(
                self.request,
                items,
                ['status', 'identifier', 'status_message', 'status_location', 'progress', 'action'],
            )

        return dict(title=self.title, description=self.description, grid=grid, items=items)

@view_defaults(permission='edit', layout='default')
class OutputDetails(MyView):
    def __init__(self, request):
        super(OutputDetails, self).__init__(request, 'Output Details')
        self.db = self.request.db

    def sort_order(self):
        """Determine what the current sort parameters are.
        """
        order = self.request.GET.get('order_col', 'title')
        order_dir = self.request.GET.get('order_dir', 'asc')
        ## if order == 'due_date':
        ##     # handle sorting of NULL values so they are always at the end
        ##     order = 'CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date'
        ## if order == 'task':
        ##     # Sort ignoring case
        ##     order += ' COLLATE NOCASE'
        order_dir = 1 if order_dir == 'asc' else -1
        return dict(order=order, order_dir=order_dir)   

    def generate_form(self, formid="deform"):
        """Generate form for publishing to catalog service"""
        from .schema import PublishSchema
        schema = PublishSchema().bind()
        return Form(
            schema,
            buttons=('publish',),
            formid=formid)

    def process_form(self, form):
        try:
            controls = self.request.POST.items()
            appstruct = form.validate(controls)

            from mako.template import Template
            templ_dc = Template(filename=os.path.join(os.path.dirname(__file__), "templates", "dc.xml"))

            record=templ_dc.render(**appstruct)
            self.request.csw.transaction(ttype="insert", typename='csw:Record', record=str(record))
        except ValidationFailure, e:
            logger.exception('validation of publish form failed')
            return dict(title=self.title, description=self.description, form=e.render())
        except:
            msg = 'Publication failed.'
            logger.exception(msg)
            self.session.flash(msg, queue='error')
        else:
            self.session.flash("Publication was successful", queue='success')
        return HTTPFound(location=self.request.route_url('output_details'))

    def process_outputs(self, jobid):
        job = self.db.jobs.find_one({'identifier': jobid})
        execution = WPSExecution(url=job['wps_url'])
        execution.checkStatus(url=job['status_location'], sleepSecs=0)
        return execution.processOutputs

    def process_output(self, jobid, outputid):
        process_outputs = self.process_outputs(jobid)
        output = next(o for o in process_outputs if o.identifier == outputid)
        return output
    
    @view_config(renderer='json', name='publish.output')
    def publish(self):
        import uuid
        outputid = self.request.params.get('outputid')
        # TODO: why use session for joid?
        jobid = self.session.get('jobid')
        result = dict()
        if identifier is not None:
            output = self.process_output(jobid, outputid)

            # TODO: who about schema.bind?
            result = dict(
                identifier = uuid.uuid4().get_urn(),
                title = output.title,
                abstract = 'nix',
                creator = authenticated_userid(self.request),
                source = output.reference,
                format = output.mimeType,
                keywords = 'one,two,three',
                )

        return result
        
    @view_config(route_name='output_details', renderer='templates/output_details.pt')
    def view(self):
        form = self.generate_form()

        if 'publish' in self.request.POST:
            return self.process_form(form)

        # TODO: this is a bit fishy ...
        if self.request.params.get('jobid') is not None:
            self.session['jobid'] = self.request.params.get('jobid')
            self.session.changed()
        self.description = self.session['jobid']

        items = []
        for output in self.process_outputs(self.session.get('jobid')):
            items.append(dict(title=output.title,
                              identifier=output.identifier,
                              mime_type = output.mimeType,
                              data = output.data,
                              reference=output.reference))

        from .grid import OutputDetailsGrid
        grid = OutputDetailsGrid(
                self.request,
                items,
                ['identifier', 'title', 'data', 'reference', 'mime_type', 'action'],
            )
        return dict(title=self.title, description=self.description,
                    grid=grid, items=items, form=form.render())
        
@view_defaults(permission='edit', layout='default') 
class MyAccount(MyView):
    def __init__(self, request):
        super(MyAccount, self).__init__(request, 'My Account', "Update your profile details.")
        self.userdb = models.User(request)

    def generate_form(self, formid="deform"):
        from .schema import CredentialsSchema
        schema = CredentialsSchema().bind()
        return Form(
            schema,
            buttons=('update',),
            formid=formid)

    def process_form(self, form):
        try:
            controls = self.request.POST.items()
            captured = form.validate(controls)

            user_id=authenticated_userid(self.request)
            user = self.userdb.by_id(user_id=user_id)
            
            inputs = []
            openid =  user.get('openid').encode('ascii', 'ignore')
            inputs.append( ('openid', openid) )
            password = captured.get('password', '').encode('ascii', 'ignore')
            inputs.append( ('password', password) )
            logger.debug('update credentials with openid=%s', openid)
            execution = self.request.wps.execute(identifier='esgf_logon',
                                    inputs=inputs,
                                    output=[('output',True),('expires',False)])
            from owslib.wps import monitorExecution
            monitorExecution(execution)
            if execution.processOutputs is not None and len(execution.processOutputs) > 1:
                credentials = execution.processOutputs[0].reference
                cert_expires = execution.processOutputs[1].data[0]
                logger.debug('cert expires %s', cert_expires)
                # Update user credentials
                self.userdb.update(
                    user_id = user_id,
                    credentials = credentials,
                    cert_expires = cert_expires,
                    update_login=False,
                    )
                logger.debug('update credentials successful, credentials=%s', credentials)
                self.request.session.flash(
                    'Credentials updated successfully',
                    queue='success',
                    )
        except ValidationFailure, e:
            logger.exception('Validation of credentials form failed.')
            return dict(title=self.title, description=self.description, form=e.render())
        except:
            msg = 'Update of credentials failed.'
            logger.exception(msg)
            self.request.session.flash(msg, queue='error')
        return HTTPFound(location=self.request.route_url('account'))
        
    @view_config(route_name='account', renderer='templates/account.pt')
    def view(self):
        user_id=authenticated_userid(self.request)
        user = self.userdb.by_id(user_id=user_id)

        from .schema import AccountSchema
        form = Form(schema=AccountSchema(), buttons=('submit',))
        creds_form = self.generate_form()

        if 'update' in self.request.POST:
            return self.process_form(creds_form)
        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                form.validate(controls)
            except ValidationFailure, e:
                logger.exception('There was an error saving your settings.')
                return dict(form = e.render())

            from peppercorn import parse
            values = parse(self.request.params.items())
            # Update the user
            update_user(
                request = self.request,
                user_id = user_id,
                name = values.get('name', u''),
                openid = values.get('openid', u''),
                organisation = values.get('organisation', u''),
                notes = values.get('notes', u''),
                update_login=False,
                )
            self.request.session.flash(
                'Settings updated successfully',
                queue='success',
                )
            return HTTPFound('/account')
        # Get existing values
        appstruct = {}
        if user is not None:
            appstruct = dict(
                email = user_id,
                openid = user.get('openid'),
                name = user.get('name'),
                organisation = user.get('organisation'),
                notes = user.get('notes'),
                credentials = user.get('credentials'),
                cert_expires = user.get('cert_expires')
                )
        return dict(
            title=self.title,
            description=self.description,
            form=form.render(appstruct),
            form_credentials=creds_form.render(appstruct))

@view_defaults(permission='edit', layout='default') 
class Map:
    def __init__(self, request):
        self.request = request
        self.userdb = models.User(self.request)

    @view_config(route_name='map', renderer='templates/map.pt')
    def map(self):
        return dict()

@view_defaults(permission='admin', layout='default')    
class Settings(MyView):
    def __init__(self, request):
        super(Settings, self).__init__(request, 'Settings', "Configure Phoenix.")
        self.settings = self.request.registry.settings

    @view_config(route_name='settings', renderer='templates/settings.pt')
    def view(self):
        buttongroups = []
        buttons = []

        buttons.append(dict(url=self.settings.get('supervisor.url'),
                            icon="monitor_edit.png", title="Supervisor", id="external-url"))
        buttons.append(dict(url="/settings/catalog", icon="catalog_pages.png", title="Catalog"))
        buttons.append(dict(url="/settings/users", icon="user_catwomen.png", title="Users"))
        buttons.append(dict(url=self.settings.get('thredds.url'),
                            icon="unidataLogo.png", title="Thredds", id="external-url"))
        buttongroups.append(dict(title='Settings', buttons=buttons))

        return dict(
            title=self.title,
            description=self.description,
            buttongroups=buttongroups)

@view_defaults(permission='admin', layout='default')
class CatalogSettings(MyView):
    
    def __init__(self, request):
        super(CatalogSettings, self).__init__(request, 'Catalog', "Configure Catalog Service (CSW).")
        self.csw = self.request.csw
        
    def generate_service_form(self, formid="deform"):
        from .schema import CatalogAddServiceSchema
        schema = CatalogAddServiceSchema()
        return Form(
            schema,
            buttons=(Button(name='add_service', title='Add Service'),),
            formid=formid)

    def process_service_form(self, form):
        try:
            controls = self.request.POST.items()
            appstruct = form.validate(controls)
            url = appstruct.get('url')
            self.request.csw.harvest(
                source=url,
                resourcetype=appstruct.get('resource_type'))
            self.session.flash('Added WPS %s' % (url), queue="success")
        except ValidationFailure, e:
            logger.exception('validation of catalog form failed')
            return dict(title=self.title, description=self.description, form = e.render())
        except Exception, e:
            logger.exception('could not harvest wps.')
            self.session.flash('Could not add WPS %s. %s' % (url, e), queue="error")
        return HTTPFound(location=self.request.route_url('catalog'))

    def generate_dataset_form(self, formid="deform"):
        from .schema import PublishSchema
        schema = PublishSchema().bind(userid=authenticated_userid(self.request))
        return Form(
            schema,
            buttons=(Button(name='add_dataset', title='Add Dataset'),),
            formid=formid)

    def process_dataset_form(self, form):
        try:
            controls = self.request.POST.items()
            appstruct = form.validate(controls)

            from mako.template import Template
            templ_dc = Template(filename=os.path.join(os.path.dirname(__file__), "templates", "dc.xml"))
            record = templ_dc.render(**appstruct)
            logger.debug('record=%s', record)
            self.request.csw.transaction(ttype="insert", typename='csw:Record', record=str(record))
            self.session.flash('Added Dataset %s' % (appstruct.get('title')), queue="success")
        except ValidationFailure, e:
            logger.exception('validation of catalog form failed')
            return dict(title=self.title, description=self.description, form = e.render())
        except Exception, e:
            logger.exception('could not harvest wps.')
            self.session.flash('Could not add WPS %s. %s' % (url, e), queue="error")
        return HTTPFound(location=self.request.route_url('catalog'))

    @view_config(renderer='json', name='delete.entry')
    def delete(self):
        identfier = self.request.params.get('identifier', None)
        self.session.flash('Delete WPS not Implemented', queue="error")
        return {}

    def get_csw_items(self):
        results = []
        try:
            self.csw.getrecords(esn="full")
            logger.debug('csw results %s', self.csw.results)
            for rec in self.csw.records:
                myrec = self.csw.records[rec]
                results.append(dict(
                    source = myrec.source,
                    identifier = myrec.identifier,
                    title = myrec.title,
                    abstract = myrec.abstract,
                    subjects = myrec.subjects,
                    format = myrec.format,
                    creator = myrec.creator,
                    modified = myrec.modified,
                    bbox = myrec.bbox,
                    references = myrec.references,
                    ))
        except:
            logger.exception('could not get items for csw.')
        return results
 
    @view_config(route_name="catalog", renderer='templates/settings/catalog.pt')
    def view(self):
        service_form = self.generate_service_form()
        dataset_form = self.generate_dataset_form()
        if 'add_service' in self.request.POST:
            return self.process_service_form(service_form)
        elif 'add_dataset' in self.request.POST:
            return self.process_dataset_form(dataset_form)
        from .grid import CatalogGrid
        items = self.get_csw_items()
            
        grid = CatalogGrid(
                self.request,
                items,
                ['title', 'source', 'abstract', 'subjects', 'format', 'action'],
            )
        return dict(
            title=self.title,
            description=self.description,
            grid=grid,
            items=items,
            service_form=service_form.render(),
            dataset_form=dataset_form.render())

@view_defaults(permission='admin', layout='default')
class UserSettings(MyView):
    def __init__(self, request):
        super(UserSettings, self).__init__(request, 'Users', "Configure Phoenix Users.")
        self.userdb = models.User(self.request)

    def sort_order(self):
        """Determine what the current sort parameters are.
        """
        order = self.request.GET.get('order_col', 'activated')
        order_dir = self.request.GET.get('order_dir', 'asc')
        ## if order == 'due_date':
        ##     # handle sorting of NULL values so they are always at the end
        ##     order = 'CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date'
        ## if order == 'task':
        ##     # Sort ignoring case
        ##     order += ' COLLATE NOCASE'
        order_dir = 1 if order_dir == 'asc' else -1
        return dict(order=order, order_dir=order_dir)   
        

    def generate_form(self, formid="deform"):
        """This helper code generates the form that will be used to add
        and edit a user based on the schema of the form.
        """
        from .schema import UserSchema
        schema = UserSchema().bind()
        options = """
        {success:
           function (rText, sText, xhr, form) {
             deform.processCallbacks();
             deform.focusFirstInput();
             var loc = xhr.getResponseHeader('X-Relocate');
                if (loc) {
                  document.location = loc;
                };
             }
        }
        """
        return Form(
            schema,
            buttons=('submit',),
            formid=formid,
            use_ajax=False,
            ajax_options=options,
            )

    def process_form(self, form):
        try:
            controls = self.request.POST.items()
            captured = form.validate(controls)

            logger.debug('update user: %s', captured)

            self.userdb.update(user_id = captured.get('user_id', ''),
                               openid = captured.get('openid', ''),
                               name = captured.get('name', ''),
                               organisation = captured.get('organisation'),
                               notes = captured.get('notes', ''))
        except ValidationFailure, e:
            logger.exception('validation of user form failed')
            return dict(title=self.title, description=self.description, form = e.render())
        return HTTPFound(location=self.request.route_url('user'))

    @view_config(renderer='json', name='delete.user')
    def delete(self):
        user_id = self.request.params.get('user_id', None)
        if user_id is not None:
            self.userdb.delete(user_id=user_id)

        return {}

    @view_config(renderer='json', name='activate.user')
    def activate(self):
        user_id = self.request.params.get('user_id', None)
        logger.debug('activate user %s' %(user_id))
        if user_id is not None:
            self.userdb.activate(user_id)

        return {}

    @view_config(renderer='json', name='edit.user')
    def edit(self):
        user_id = self.request.params.get('user_id', None)
        result = dict(user_id=user_id)
        logger.debug('edit user %s' % (user_id))
        if user_id is not None:
            user = self.userdb.by_id(user_id=user_id)
            result = dict(
                user_id = user_id,
                openid = user.get('openid'),
                name = user.get('name'),
                organisation = user.get('organisation'),
                notes = user.get('notes'),
                )

        return result

    @view_config(route_name='user_settings', renderer='templates/settings/users.pt')
    def view(self):
        form = self.generate_form()
        if 'submit' in self.request.POST:
            return self.process_form(form)

        from .grid import UsersGrid
        order = self.sort_order()
        user_items = self.userdb.all(key=order.get('order'), direction=order.get('order_dir'))
        grid = UsersGrid(
                self.request,
                user_items,
                ['name', 'user_id', 'openid', 'organisation', 'notes', 'activated', 'action'],
            )
        return dict(
            title=self.title,
            description=self.description,
            grid=grid,
            items=user_items,
            form=form.render())

