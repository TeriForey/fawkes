from pyramid.view import view_config, view_defaults

from owslib.wps import WebProcessingService

from phoenix.views import MyView
from phoenix.utils import wps_caps_url


@view_defaults(permission='view', layout="default")
class ProcessList(MyView):
    def __init__(self, request):
        self.service_name = request.registry.settings['namewps']
        self.wps = WebProcessingService(
            url=request.route_url('owsproxy', service_name=self.service_name),
            verify=False)
        super(ProcessList, self).__init__(request, name='namewps_list', title='')

    @view_config(route_name='namewps_list', renderer='../templates/list.pt', accept='text/html')
    def view(self):
        items = []
        for process in self.wps.processes:
            item = dict(
                title="{0.title} {0.processVersion}".format(process),
                description=getattr(process, 'abstract', ''),
                url=self.request.route_path('processes_execute',
                                            _query=[('wps', self.service_name), ('process', process.identifier)]))
            items.append(item)
        return dict(
            url=wps_caps_url(self.wps.url),
            title=self.wps.identification.title,
            description=self.wps.identification.abstract,
            provider_name=self.wps.provider.name,
            provider_site=self.wps.provider.url,
            items=items)
