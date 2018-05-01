def includeme(config):
    # settings = config.registry.settings

    config.add_route('namewps_list', '/namewps')
    # config.add_route('namewps_list', '/namewps/list')
    # config.add_route('processes_execute', '/processes/execute')
    #
    # config.include('phoenix.processes.views.actions')
