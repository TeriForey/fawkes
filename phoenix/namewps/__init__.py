def includeme(config):
    # settings = config.registry.settings

    config.add_route('namewps_list', '/namewps')
    # config.add_route('namewps_list', '/namewps/list')
    config.add_route('namewps_execute', '/namewps/execute')
    #
    # config.include('phoenix.processes.views.actions')
