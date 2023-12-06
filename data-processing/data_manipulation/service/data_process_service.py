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
import ulid
import traceback

from common import log_tag_const
from data_store_process import minio_store_process
from database_operate import (
    data_process_db_operate,
    data_process_detail_db_operate
)
from kube import dataset_cr
from parallel import thread_parallel
from utils import date_time_utils

logger = logging.getLogger(__name__)


def list_by_page(req_json, opt={}):
    """Get the list data for data processing by page"""
    return data_process_db_operate.list_by_page(req_json, opt)


def list_by_count(req_json, opt={}):
    """Get count for the list data processing with page"""
    return data_process_db_operate.list_by_count(req_json, opt)


def add(req_json, opt={}):
    """Add a new data process task.
    
    req_json is a dictionary object. for example:
    {
        "name": "小T_test_0201",
        "file_type": "text",
        "pre_data_set_name": "dataset1",
        "pre_data_set_version": "v2",
        "post_data_set_name": "dataset1",
        "post_data_set_version": "v2",
        "version_data_set_name": "dataset1-v2",
        "bucket_name": "system-tce",
        "file_names": [
            {
                "name": "数据处理文件_小T.pdf"
            }
        ],
        "data_process_config_info": []
    } 

    opt is a dictionary object. It has the following keys:
    pool: database connection pool.
    """
    id = ulid.ulid()
    opt['id'] = id
    res = data_process_db_operate.add(req_json, opt)

    if res['status'] == 200:
        # update the dataset status
        update_dataset = dataset_cr.update_dataset_k8s_cr({
            'bucket_name': req_json['bucket_name'],
            'version_data_set_name': req_json['version_data_set_name'],
            'reason': 'processing'
        })

        if update_dataset['status'] != 200:
            return update_dataset

        try:

            async def async_text_manipulate(req_json, opt):
                minio_store_process.text_manipulate(req_json, opt)

            def execute_text_manipulate_task(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(async_text_manipulate(req_json, opt))

            thread_parallel.run_async_background_task(
                execute_text_manipulate_task,
                'execute text manipuate task'
            )
        except Exception as ex:
            logger.error(''.join([
                f"{log_tag_const.MINIO_STORE_PROCESS} There is an error when ",
                f"start to run the minio store process.\n",
                f"{traceback.format_exc()}\n"
            ]))
        

    
    return res


def delete_by_id(req_json, opt={}):
    """Delete a record with id"""
    return data_process_db_operate.delete_by_id(req_json, opt)


def info_by_id(req_json, opt={}):
    """Get a detail info with id.

    req_json is a dictionary object. for example:
    {
        "id": "01HGWBE48DT3ADE9ZKA62SW4WS"
    }
    """
    id = req_json['id']

    data = _get_default_data_for_detail()
    _get_and_set_basic_detail_info(data, {
        'task_id': id,
        'conn_pool': opt['pool']
    })

    if data['id'] == '':
        return  {
            'status': 200,
            'message': '',
            'data': data
        }

    process_cofig_map = _convert_config_info_to_map(data.get('data_process_config_info'))

    config_map_for_result = {}
    _set_basic_info_for_config_map_for_result(config_map_for_result, process_cofig_map)

    _set_children_info_for_config_map_for_result(
        config_map_for_result, 
        process_cofig_map, {
            'task_id': id,
            'conn_pool': opt['pool']
        }
    )

    # convert the conig resule from map to list
    config_list_for_result = []
    for value in config_map_for_result.values():
        config_list_for_result.append(value)
    
    data['config'] = config_list_for_result

    logger.debug(f"{log_tag_const.DATA_PROCESS_DETAIL} The response data is: \n{data}")

    return  {
        'status': 200,
        'message': '',
        'data': data
    }


def _get_default_data_for_detail():
    """Get the data for the detail"""
    return {
        "id": "",
        "name": "", 
        "status": "",
        "file_type": "",
        "pre_dataset_name": "",
        "pre_dataset_version": "",
        "post_dataset_name": "",
        "post_dataset_version": "",
        "file_num": 0,
        "start_time": '',
        "end_time": '',
        "data_process_config_info": [],
        "config": []
    }


def _get_and_set_basic_detail_info(from_result, opt):
    """Get and set the basic detail info.
    
    from_result: the from result, it's content will be changed;

    opt is a dictionary object. It has the following keys:
    task_id: task id;
    conn_pool: database connection pool
    """
    # step 1
    # Get the detail info from the database.
    detail_info_params = {
        'id': opt['task_id']
    }
    detail_info_res = data_process_db_operate.info_by_id(detail_info_params, {
        'pool': opt['conn_pool']
    })
    if detail_info_res['status'] == 200 and len(detail_info_res['data']) > 0:
        detail_info_data = detail_info_res['data'][0]

        file_num = 0
        if detail_info_data.get('file_names'):
            file_num = len(detail_info_data['file_names'])
        
        from_result['id'] = opt['task_id']
        from_result['name'] = detail_info_data['name']
        from_result['status'] = detail_info_data['status']
        from_result['file_type'] = detail_info_data['file_type']
        from_result['file_num'] = file_num
        from_result['pre_dataset_name'] = detail_info_data['pre_data_set_name']
        from_result['pre_dataset_version'] = detail_info_data['pre_data_set_version']
        from_result['post_dataset_name'] = detail_info_data['post_data_set_name']
        from_result['post_dataset_version'] = detail_info_data['post_data_set_version']
        from_result['start_time'] = detail_info_data['start_datetime']
        from_result['end_time'] = detail_info_data['end_datetime']
        from_result['data_process_config_info'] = detail_info_data['data_process_config_info']
    else:
        from_result['id'] = ''


def _convert_config_info_to_map(config_info_list):
    """Convert the config info to map.

        config_info_list: a list for example
        [
            {
                "type": "qa_split"
            },
            {
                "type": "remove_invisible_characters"
            },
            {
                "type": "space_standardization"
            },
            {
                "type": "remove_email"
            }
        ]
    """
    result = {}
    for item in config_info_list:
        result[item['type']] = 1

    return result


def _set_basic_info_for_config_map_for_result(from_result, process_cofig_map):
    """Set basic info for the config map for result.
    
    from_result: the from result, it's content will be changed.
    process_config_map: process config map 
    """
    # chunk processing
    if process_cofig_map.get('qa_split'):
        if from_result.get('chunk_processing') is None:
            from_result['chunk_processing'] = {
                'name': 'chunk_processing',
                'description': '拆分处理',
                'status': 'succeed',
                'children': []
            }

    # data clean
    if process_cofig_map.get('remove_invisible_characters') or \
       process_cofig_map.get('space_standardization') or \
       process_cofig_map.get('traditional_to_simplified') or \
       process_cofig_map.get('space_standremove_html_tagardization'):
        if from_result.get('clean') is None:
            from_result['clean'] = {
                    'name': 'clean',
                    'description': '异常清洗配置',
                    'status': 'succeed',
                    'children': []
                }
            
    # remove privacy
    if process_cofig_map.get('remove_email'):
        if from_result.get('privacy') is None:
            from_result['privacy'] = {
                'name': 'privacy',
                'description': '数据隐私处理',
                'status': 'succeed',
                'children': []
            }    


def _set_children_info_for_config_map_for_result(from_result, process_cofig_map, opt):
    """Set child list for the config for result
    
    from_result: the from result, it's content will be changed.
    process_config_map: process config map;
    opt is a dictionary object. It has the following keys:
    task_id: task id,
    conn_pool: database connection pool 
    """
    # insert the qa list
    if process_cofig_map.get('qa_split'):
        from_result['chunk_processing']['children'].append({
            'name': 'qa_split',
            'enable': 'true',
            'zh_name': 'QA拆分',
            'description': '根据文件中的文章与图表标题，自动将文件做 QA 拆分处理。',
            'preview': _get_qa_list_preview({
                'task_id': opt['task_id'],
                'conn_pool': opt['conn_pool']
            })
        })

    # remove invisible characters
    if process_cofig_map.get('remove_invisible_characters'):
        from_result['clean']['children'].append({
            'name': 'remove_invisible_characters',
            'enable': 'true',
            'zh_name': '移除不可见字符',
            'description': '移除ASCII中的一些不可见字符, 如0-32 和127-160这两个范围',
            'preview': _get_transform_preview_list({
                'task_id': opt['task_id'],
                'transform_type': 'remove_invisible_characters',
                'conn_pool': opt['conn_pool']
            })
        })       

    # space standardization
    if process_cofig_map.get('space_standardization'):
        from_result['clean']['children'].append({
            'name': 'space_standardization',
            'enable': 'true',
            'zh_name': '空格处理',
            'description': '将不同的unicode空格比如u2008, 转成正常的空格',
            'preview': _get_transform_preview_list({
                'task_id': opt['task_id'],
                'transform_type': 'space_standardization',
                'conn_pool': opt['conn_pool']
            })
        })   

    # remove email
    if process_cofig_map.get('remove_email'):
        from_result['privacy']['children'].append({
            'name': 'remove_email',
            'enable': 'true',
            'zh_name': '去除Email',
            'description': '去除email地址',
            'preview': _get_transform_preview_list({
                'task_id': opt['task_id'],
                'transform_type': 'remove_email',
                'conn_pool': opt['conn_pool']
            })
        })



def _get_transform_preview_list(opt={}):
    """"Get transofm preview list.
    
    opt is a dictionary object. It has the following keys:
    task_id: task id;
    transform_type: transform type
    conn_pool: database connection pool;
    """
    transform_preview = []
    # step 1
    # list file name in transform
    list_file_name_params = {
        'task_id': opt['task_id'],
        'transform_type': opt['transform_type']
    }
    list_file_name_res = data_process_detail_db_operate.list_file_name_for_transform(
        list_file_name_params, {
        'pool': opt['conn_pool']
    })
    if list_file_name_res['status'] == 200:
        for item in list_file_name_res['data']:
            transform_preview.append({
                'file_name': item['file_name'],
                'content': []
            })
    # step 2
    # iterate the transform preview
    for item in transform_preview:
        list_transform_params = {
            'task_id': opt['task_id'],
            'transform_type': opt['transform_type'],
            'file_name': item['file_name']
        }
        list_transform_res = data_process_detail_db_operate.top_n_list_transform_for_preview(
            list_transform_params, {
                'pool': opt['conn_pool']
            }
        )
        if list_transform_res['status'] == 200:
            for item_transform in list_transform_res['data']:
                item['content'].append({
                    'pre': item_transform['pre_content'],
                    'post': item_transform['post_content']
                })
    
    return transform_preview


def _get_qa_list_preview(opt={}):
    """Get the QA list preview.
    
    opt is a dictionary object. It has the following keys:
    task_id: task od;
    conn_pool: database connection pool
    """
    qa_list_preview = []
    # step 1
    # list file name in QA
    list_file_name_params = {
        'task_id': opt['task_id']
    }
    list_file_name_res = data_process_detail_db_operate.list_file_name_in_qa_by_task_id(
        list_file_name_params, {
            'pool': opt['conn_pool']
        }
    )
    if list_file_name_res['status'] == 200:
        for item in list_file_name_res['data']:
            qa_list_preview.append({
                'file_name': item['file_name'],
                'content': []
            })
    
    # step 2
    # iterate the QA list preview
    for item in qa_list_preview:
        list_qa_params = {
            'task_id': opt['task_id'],
            'file_name': item['file_name']
        }
        list_qa_res = data_process_detail_db_operate.top_n_list_qa_for_preview(
            list_qa_params, {
                'pool': opt['conn_pool']
            }
        )
        if list_qa_res['status'] == 200:
            for item_qa in list_qa_res['data']:
                item['content'].append({
                    'pre': item_qa['question'],
                    'post': item_qa['answer']
                })
        
    return qa_list_preview



