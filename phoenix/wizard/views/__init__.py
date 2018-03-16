from pyramid.view import view_defaults
from pyramid.httpexceptions import HTTPFound

from deform import Form, Button
from deform import ValidationFailure

from phoenix.views import MyView
from phoenix.utils import skip_csrf_token
from phoenix.security import check_csrf_token

import logging
LOGGER = logging.getLogger("PHOENIX")

wizard_favorite = "wizard_favorite"


class WizardFavorite(object):
    """Stores wizard state in session with a name (favorite).
    TODO: implement as a dict?
    """
    def __init__(self, request, session):
        self.request = request
        self.session = session
        if wizard_favorite not in self.session:
            self.clear()

    def names(self):
        return self.session[wizard_favorite].keys()

    def get(self, name):
        return self.session[wizard_favorite].get(name)

    def set(self, name, state):
        if name and state:
            self.session[wizard_favorite][name] = state
            self.session.changed()

    def clear(self):
        self.session[wizard_favorite] = {}
        self.session.changed()


class WizardState(object):
    def __init__(self, session, initial_step='wizard', final_step='wizard_done'):
        self.session = session
        self.initial_step = initial_step
        self.final_step = final_step
        if 'wizard' not in self.session:
            self.clear()

    def load(self, state):
        import copy
        self.clear()
        self.session['wizard']['state'] = copy.deepcopy(state)
        self.session.changed()

    def dump(self):
        return self.session['wizard']['state']

    def current_step(self):
        step = self.initial_step
        if len(self.session['wizard']['chain']) > 0:
            step = self.session['wizard']['chain'][-1]
        return step

    def is_first(self):
        return self.current_step() == self.initial_step

    def is_last(self):
        return self.current_step() == self.final_step

    def next(self, step):
        self.session['wizard']['chain'].append(step)
        self.session.changed()

    def previous(self):
        if len(self.session['wizard']['chain']) > 1:
            self.session['wizard']['chain'].pop()
            self.session.changed()

    def get(self, key, default=None):
        if self.session['wizard']['state'].get(key) is None:
            self.session['wizard']['state'][key] = default
            self.session.changed()
        return self.session['wizard']['state'].get(key)

    def set(self, key, value):
        self.session['wizard']['state'][key] = value
        self.session.changed()

    def clear(self):
        self.session['wizard'] = dict(state={}, chain=[self.initial_step])
        self.session.changed()


@view_defaults(permission='submit', layout='default')
class Wizard(MyView):
    def __init__(self, request, name, title, description=None):
        super(Wizard, self).__init__(request, name, title, description)
        self.wizard_state = WizardState(self.session)
        self.favorite = WizardFavorite(self.request, self.session)

    def buttons(self):
        prev_disabled = not self.prev_ok()
        next_disabled = not self.next_ok()

        prev_button = Button(name='previous', title='Previous',
                             css_class="btn-warning",
                             disabled=prev_disabled)   # type=submit|reset|button,value=name,css_type="btn-..."
        cancel_button = Button(name='cancel', title='Cancel',
                               css_class='btn-danger',
                               disabled=False)
        next_button = Button(name='next', title='Next',
                             css_class="btn-success",
                             disabled=next_disabled)
        done_button = Button(name='next', title='Done',
                             css_class="btn-success",
                             disabled=next_disabled or not self.request.has_permission('submit'))

        buttons = []
        # TODO: fix focus button
        if not self.wizard_state.is_first():
            buttons.append(prev_button)
            buttons.append(cancel_button)
        if self.wizard_state.is_last():
            buttons.append(done_button)
        else:
            buttons.append(next_button)
        return buttons

    def prev_ok(self):
        return True

    def next_ok(self):
        return True

    def use_ajax(self):
        return False

    def ajax_options(self):
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
        return options

    def success(self, appstruct):
        self.wizard_state.set(self.name, skip_csrf_token(appstruct))

    def appstruct(self):
        return self.wizard_state.get(self.name, {})

    def schema(self):
        raise NotImplementedError

    def previous_success(self, appstruct):
        # TODO: maybe store current state?
        # self.success(appstruct)
        return self.previous()

    def previous_failure(self, validation_failure):
        # don't stop previous in case of validation failure
        return self.previous()

    def next_success(self, appstruct):
        raise NotImplementedError

    def next_failure(self, validation_failure):
        custom = self.custom_view()  # TODO: need a better way for this
        return dict(title=self.title, form=validation_failure.render(), **custom)

    def generate_form(self, formid='deform'):
        return Form(
            schema=self.schema(),
            buttons=self.buttons(),
            formid=formid,
            use_ajax=self.use_ajax(),
            ajax_options=self.ajax_options(),
        )

    def process_form(self, form, action):
        success_method = getattr(self, '%s_success' % action)
        failure_method = getattr(self, '%s_failure' % action)
        try:
            controls = self.request.POST.items()
            LOGGER.debug("before validate controls=%s", controls)
            appstruct = form.validate(controls)
            LOGGER.debug("before success appstruct=%s", appstruct)
            result = success_method(appstruct)
        except ValidationFailure as e:
            LOGGER.exception('Validation of wizard view failed.')
            result = failure_method(e)
        return result

    def previous(self):
        self.wizard_state.previous()
        return HTTPFound(location=self.request.route_path(self.wizard_state.current_step()))

    def next(self, step, query=None):
        self.wizard_state.next(step)
        return HTTPFound(location=self.request.route_path(self.wizard_state.current_step(), _query=query))

    def cancel(self):
        self.wizard_state.clear()
        return HTTPFound(location=self.request.route_path(self.wizard_state.current_step()))

    def custom_view(self):
        return {}

    def breadcrumbs(self):
        breadcrumbs = super(Wizard, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path('wizard'), title='Wizard'))
        return breadcrumbs

    def resources(self):
        resources = []
        # TODO: Do I need this resource?
        # resource = self.wizard_state.get('wizard_source')['source']
        return resources

    def view(self):
        form = self.generate_form()

        if 'previous' in self.request.POST:
            check_csrf_token(self.request)
            return self.process_form(form, 'previous')
        elif 'next' in self.request.POST:
            check_csrf_token(self.request)
            return self.process_form(form, 'next')
        elif 'cancel' in self.request.POST:
            check_csrf_token(self.request)
            return self.cancel()
        result = dict(title=self.title, form=form.render(self.appstruct()))
        custom = self.custom_view()
        return dict(result, **custom)
