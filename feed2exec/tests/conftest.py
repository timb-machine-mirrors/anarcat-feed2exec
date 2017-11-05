import betamax

with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'feed2exec/tests/cassettes/'
    # config.default_cassette_options['record_mode'] = 'new_episodes'
