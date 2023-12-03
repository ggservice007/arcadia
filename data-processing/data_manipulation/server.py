# Copyright 2023 KubeAGI.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import asyncio
import logging
import time

import psycopg2
from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS

from common import config, log_tag_const
from service import data_process_service
from transform.text import support_type
from utils import log_utils, sanic_utls
from database_clients import postgresql_pool_client


# Initialize the log config
log_utils.init_config({
    'source_type': 'manipulate_server',
    'log_dir': "log"
})

logger = logging.getLogger('manipulate_server')

app = Sanic(name='data_manipulate')
CORS(app)
app.error_handler = sanic_utls.CustomErrorHandler()


@app.middleware('request')
async def request_start_time_middleware(request):
    """Middleware to record request start time and status code"""
    request.ctx.start_time = time.time()


@app.middleware('response')
async def request_processing_time_middleware(request, response):
    """Middleware to calculate and log request processing time and status code"""
    processing_time = time.time() - request.ctx.start_time
    logger.debug(''.join([
        f"{log_tag_const.WEB_SERVER_ACCESS} {request.method.lower()} {request.url} "
        f"{response.status} {processing_time:.4f} seconds"
    ]))
    return response


@app.listener('before_server_start')
async def init_web_server(app, loop):
    app.config['REQUEST_MAX_SIZE'] = 1024 * 1024 * 1024  # 1G
    app.config['REQUEST_TIMEOUT'] = 60 * 60 * 60
    app.config['RESPONSE_TIMEOUT'] = 60 * 60 * 60
    app.config['KEEP_ALIVE_TIMEOUT'] = 60 * 60 * 60
    app.config['conn_pool'] = postgresql_pool_client.get_pool(_create_database_connection)


@app.listener('after_server_stop')
async def shutdown_web_server(app, loop):
    postgresql_pool_client.release_pool(app.config['conn_pool'])


@app.route('list-by-page', methods=['POST'])
async def list_by_page(request):
    res = await data_process_service.list_by_page(request.json, {
        'pool': app.config['conn_pool']
    })
    return json(res)


@app.route('list-by-count', methods=['POST'])
async def list_by_count(request):
    res = await data_process_service.list_by_count(request.json, {
        'pool': app.config['conn_pool']
    })
    return json(res)


@app.route('add', methods=['POST'])
async def add(request):
    res = await data_process_service.add(request.json, {
        'pool': app.config['conn_pool'],
        'sanic_app': app
    })
    return json(res)


@app.route('delete-by-id', methods=['POST'])
async def delete_by_id(request):
    res = await data_process_service.delete_by_id(request.json, {
        'pool': app.config['conn_pool']
    })
    return json(res)


@app.route('info-by-id', methods=['POST'])
async def info_by_id(request):
    res = await data_process_service.info_by_id(request.json, {
        'pool': app.config['conn_pool']
    })
    return json(res) 


@app.route('text-process-type', methods=['POST'])
async def text_process_type(request):
    """Get the support type for transforming the text content"""
    return json({
        'status': 200,
        'message': '',
        'data': support_type.support_types
    })



def _create_database_connection():
    """Create a database connection."""
    return psycopg2.connect(
                host=config.pg_host, 
                port=config.pg_port,
                user=config.pg_user,
                password=config.pg_password, 
                database=config.pg_database
            )




if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=28888,
            access_log=False,
            debug=False,
            workers=2)
