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


import ujson
import ulid
from sanic.response import json

from database_clients import postgresql_pool_client
from utils import date_time_utils

async def list_by_page(req_json, opt={}):
    """Get the list data for data processing by page"""
    pool = opt['pool']
    
    params = {
        'keyword': '%' + req_json['keyword'] + '%',
        'pageIndex': int(req_json['pageIndex']),
        'pageSize': int(req_json['pageSize'])
    }

    sql = """
        select
          id,
          name,
          status,
          pre_data_set_name,
          pre_data_set_version,
          post_data_set_name,
          post_data_set_version,
          start_datetime
        from
          public.data_process_task
        where
          name like %(keyword)s
        order by start_datetime desc
        limit %(pageSize)s offset %(pageIndex)s
    """.strip()

    res = await postgresql_pool_client.execute_query(pool, sql, params)
    return res


async def list_by_count(req_json, opt={}):
    """Get count for the list data processing with page"""
    pool = opt['pool']
    
    params = {
        'keyword': '%' + req_json['keyword'] + '%'
    }

    sql = """
        select
          count(*)
        from
          public.data_process_task
        where
          name like %(keyword)s
    """.strip()

    res = await postgresql_pool_client.execute_count_query(pool, sql, params)
    return res


async def delete_by_id(req_json, opt={}):
    """Delete a record with id"""
    pool = opt['pool']

    params = {
        'id': req_json['id']
    }

    sql = """
        delete from public.data_process_task 
        where
          id = %(id)s
    """.strip()

    res =  await postgresql_pool_client.execute_update(pool, sql, params)
    return res


async def add(req_json, opt={}):
    """Add a new record"""
    pool = opt['pool']
    
    now = date_time_utils.now_str()
    user = 'admin'
    program = '数据处理任务-新增'

    params = {
        'id': opt['id'],
        'name': req_json['name'],
        'file_type': req_json['file_type'],
        'status': 'processing',
        'pre_data_set_name': req_json['pre_data_set_name'],
        'pre_data_set_version': req_json['pre_data_set_version'],
        'file_names': ujson.dumps(req_json['file_names']),
        'post_data_set_name': req_json['post_data_set_name'],
        'post_data_set_version': req_json['post_data_set_version'],
        'data_process_config_info': ujson.dumps(req_json['data_process_config_info']),
        'start_datetime': now,
        'create_datetime': now,
        'create_user': user,
        'create_program': program,
        'update_datetime': now,
        'update_user': user,
        'update_program': program
    }

    sql = """
        insert into public.data_process_task (
          id,
          name,
          file_type,
          status,
          pre_data_set_name,
          pre_data_set_version,
          file_names,
          post_data_set_name,
          post_data_set_version,
          data_process_config_info,
          start_datetime,
          create_datetime,
          create_user,
          create_program,
          update_datetime,
          update_program,
          update_user
        )
        values (
          %(id)s,
          %(name)s,
          %(file_type)s,
          %(status)s,
          %(pre_data_set_name)s,
          %(pre_data_set_version)s,
          %(file_names)s,
          %(post_data_set_name)s,
          %(post_data_set_version)s,
          %(data_process_config_info)s,
          %(start_datetime)s,
          %(create_datetime)s,
          %(create_program)s,
          %(create_user)s,
          %(update_datetime)s,
          %(update_program)s,
          %(update_user)s 
        )
    """.strip()

    res =  await postgresql_pool_client.execute_update(pool, sql, params)
    return res


async def update_status_by_id(req_json, opt={}):
    """Update the status with id"""
    pool = opt['pool']

    now = date_time_utils.now_str()
    user = 'admin'
    program = '修改任务状态'

    params = {
        'id': req_json['id'],
        'status': req_json['status'],
        'end_datetime': now,
        'update_datetime': now,
        'update_program': program,
        'update_user': user
    }

    sql = """
        update public.data_process_task set
          status = %(status)s,
          update_datetime = %(update_datetime)s,
          end_datetime = %(end_datetime)s,
          update_program = %(update_program)s,
          update_user = %(update_user)s
        where
          id = %(id)s
    """.strip()

    res =  await postgresql_pool_client.execute_update(pool, sql, params)
    return res


async def info_by_id(req_json, opt={}):
    """info with id"""
    pool = opt['pool']

    params = {
        'id': req_json['id']
    }

    sql = """
        select
          id,
          name,
          file_type,
          status,
          pre_data_set_name,
          pre_data_set_version,
          post_data_set_name,
          post_data_set_version,
          file_names,
          data_process_config_info,
          start_datetime,
          end_datetime,
          create_user,
          update_datetime
        from
          public.data_process_task
        where
          id = %(id)s
    """.strip()

    res = await postgresql_pool_client.execute_query(pool, sql, params)
    return res