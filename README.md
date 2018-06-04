dp-conceptual-search
==================

# TODO

* Test randomness of word vectors upon training of new model
* Install NLP plugin and add entities search to base content query

# Configuration

### Environment variales

| Environment variable         | Default                 | Description
| ---------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------
| SEARCH_CONFIG                | development             | Specifies which config_*.py file to use.
| ELASTIC_SEARCH_ASYNC_ENABLED | true                    | Specify whether to use synchronous or asynchronous Elasticsearch client.
| ELASTIC_SEARCH_SERVER        | http://localhost:9200   | URL of Elasticsearch cluster.
| ELASTIC_SEARCH_TIMEOUT       | 1000                    | Timeout of Elasticsearch requests in seconds.
| SEARCH_INDEX                 | ons*                    | The Elasticsearch index to be queried.
| BIND_HOST                    | 0.0.0.0                 | The host to bind to.
| BIND_PORT                    | 5000                    | The port to bind to.
| CONCEPTUAL_SEARCH_ENABLED    | false                   | Enable/disable conceptual search (requires fastText models).

# Running

There are two options for running the server:
Use ```python manager.py``` to use the internal Sanic server, or  ```./run_gunicorn.sh``` to initialise as a 
gunicorn server (supports multi-processing for multiple workers and threads per worker).

# Testing

To run the tests use: ```python manager.py test```

### Licence

Copyright ©‎ 2016, Office for National Statistics (https://www.ons.gov.uk)

Released under MIT license, see [LICENSE](LICENSE.md) for details.
