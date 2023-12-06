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


import logging
import os
import pandas as pd
import traceback
import ulid

from common import config, log_tag_const
from database_operate import data_process_detail_db_operate
from llm_api_service import zhi_pu_ai_service
from llm_data_helper import text_split_helper
from transform.text import clean_transform, privacy_transform
from utils import (
    csv_utils, 
    file_utils,
    pdf_utils
)


logger = logging.getLogger(__name__)


def text_manipulate(opt={}):
    """Manipulate the text content from a pdf file.
    
    opt is a dictionary object. It has the following keys:
    file_name: file name;
    support_type: support type;
    conn_pool: database connection pool;
    task_id: data process task id;
    chunk_size: chunk size;
    chunk_overlap: chunk overlap;
    """
    
    logger.debug(f"{log_tag_const.PDF_HANDLE} Start to manipulate the text in pdf")

    try:
        file_name = opt['file_name']
        support_type = opt['support_type']
        
        pdf_file_path = file_utils.get_temp_file_path()
        file_path = pdf_file_path + 'original/' + file_name
        
        # step 1
        # Get the content from the pdf fild.
        content = pdf_utils.get_content({
            "file_path": file_path
        })
        logger.debug(f"{log_tag_const.PDF_HANDLE} The pdf content is\n {content}")

        support_type_map = _convert_support_type_to_map(support_type)
        
        # step 2
        # Clean the data such as removing invisible characters.
        clean_result = _data_clean({
            'support_type_map': support_type_map,
            'file_name': file_name,
            'data': content,
            'conn_pool': opt['conn_pool'],
            'task_id': opt['task_id']
        })

        if clean_result['status'] == 200:
            content = clean_result['data']

        # step 3
        # Remove the privacy info such as removing email.
        clean_result = _remove_privacy_info({
            'support_type_map': support_type_map,
            'file_name': file_name,
            'data': content,
            'conn_pool': opt['conn_pool'],
            'task_id': opt['task_id']
        })

        if clean_result['status'] == 200:
            content = clean_result['data']


        
        # 数据量
        object_count = 0
        object_name = ''
        if support_type_map.get('qa_split'):
            logger.debug(f"{log_tag_const.QA_SPLIT} Start to split QA.")

            qa_data = _generate_qa_list({
                'chunk_size': opt['chunk_size'],
                'chunk_overlap': opt['chunk_overlap'],
                'support_type': support_type,
                'data': content
            })

            logger.debug(f"{log_tag_const.QA_SPLIT} The QA data is: \n{qa_data}\n")

            # start to insert qa data
            for i in range(len(qa_data)):
                if i == 0:
                    continue
                qa_insert_item = {
                    'id': ulid.ulid(),
                    'task_id': opt['task_id'],
                    'file_name': file_name,
                    'question': qa_data[i][0],
                    'answer': qa_data[i][1]
                }
               
                data_process_detail_db_operate.insert_question_answer_info(
                    qa_insert_item, {
                        'pool': opt['conn_pool']
                    }
                )

            # Save the csv file.        
            file_name_without_extension = file_name.rsplit('.', 1)[0] + '_final'
            csv_utils.save_csv({
                'file_name':  file_name_without_extension + '.csv',
                'phase_value': 'final',
                'data': qa_data
            })
            
            object_name = file_name_without_extension + '.csv'
            # 减 1 是为了去除表头
            object_count = len(qa_data) - 1
            
            logger.debug(f"{log_tag_const.QA_SPLIT} Finish splitting QA.")
        
        logger.debug(f"{log_tag_const.PDF_HANDLE} Finish manipulating the text in pdf")
        return {
            'status': 200,
            'message': '',
            'data': {
                'object_name': object_name,
                'object_count': object_count
            }
        }
    except Exception as ex:
        logger.error(''.join([
            f"{log_tag_const.PDF_HANDLE} There is an error when manipulate ",
            f"the text in pdf handler. \n{traceback.format_exc()}"
        ]))
        logger.debug(f"{log_tag_const.PDF_HANDLE} Finish manipulating the text in pdf")
        return {
            'status': 400,
            'message': str(ex),
            'data': traceback.format_exc()
        }


def _data_clean(opt={}):
    """Clean the data.
    
    opt is a dictionary object. It has the following keys:
    support_type_map: example
        {
            "qa_split": 1, 
            "remove_invisible_characters": 1, 
            "space_standardization": 1, 
            "remove_email": 1
        }
    data: data;
    file_name: file name;
    conn_pool: database connection pool;
    task_id: data process task id;
    """
    support_type_map = opt['support_type_map']
    data = opt['data']

    # remove invisible characters
    if support_type_map.get('remove_invisible_characters'):
        result = clean_transform.remove_invisible_characters({
            'text': data
        })
        if result['status'] == 200:
            if result['data']['found'] > 0:
                task_detail_item = {
                    'id': ulid.ulid(),
                    'task_id': opt['task_id'],
                    'file_name': opt['file_name'],
                    'transform_type': 'remove_invisible_characters',
                    'pre_content': data,
                    'post_content': result['data']['text']
                }
                data_process_detail_db_operate.insert_transform_info(
                    task_detail_item, {
                        'pool': opt['conn_pool']
                    }
                )
            data = result['data']['text']

    
    # process for space standardization
    if support_type_map.get('space_standardization'):
        result = clean_transform.space_standardization({
            'text': data
        })
        if result['status'] == 200:
            if result['data']['found'] > 0:
                task_detail_item = {
                    'id': ulid.ulid(),
                    'task_id': opt['task_id'],
                    'file_name': opt['file_name'],
                    'transform_type': 'remove_invisible_characters',
                    'pre_content': data,
                    'post_content': result['data']['text']
                }
                data_process_detail_db_operate.insert_transform_info(
                    task_detail_item, {
                        'pool': opt['conn_pool']
                    }
                )
            data = result['data']['text']

    return {
        'status': 200,
        'message': '',
        'data': data
    }


def _remove_privacy_info(opt={}):
    """"Remove the privacy info such as removing email.
    
    opt is a dictionary object. It has the following keys:
    support_type_map: example
        {
            "qa_split": 1, 
            "remove_invisible_characters": 1, 
            "space_standardization": 1, 
            "remove_email": 1
        }
    data: data;
    file_name: file name;
    conn_pool: database connection pool;
    task_id: data process task id;
    """
    support_type_map = opt['support_type_map']
    data = opt['data']

    # remove email
    if support_type_map.get('remove_email'):
        result = privacy_transform.remove_email({
            'text': data
        })
        if result['status'] == 200:
            if result['data']['found'] > 0:
                task_detail_item = {
                    'id': ulid.ulid(),
                    'task_id': opt['task_id'],
                    'file_name': opt['file_name'],
                    'transform_type': 'remove_email',
                    'pre_content': data,
                    'post_content': result['data']['text']
                }
                data_process_detail_db_operate.insert_transform_info(
                    task_detail_item, {
                        'pool': opt['conn_pool']
                    }
                )
            data = result['data']['text']
        
   
    return {
        'status': 200,
        'message': '',
        'data': data
    }



def _generate_qa_list(opt={}):
    """Generate the Question and Answer list.
    
    opt is a dictionary object. It has the following keys:
    chunk_size: chunck size;
    chunk_overlap: chunk overlap;
    data: the text used to generate QA;
    """
    # step 1
    # Split the text.
    chunk_size = config.knowledge_chunk_size
    if opt.get('chunk_size') is not None:
        chunk_size = opt.get('chunk_size')

    chunk_overlap = config.knowledge_chunk_overlap 
    if opt.get('chunk_overlap') is not None:
        chunk_overlap = opt.get('chunk_overlap')

    text_splitter = text_split_helper.init_spacy_text_splitter({
        'separator': "\n\n",
        'chunk_size': chunk_size,
        'chunk_overlap': chunk_overlap
    })
    texts = text_split_helper.get_splitted_text_by_spacy(text_splitter, {
        'data': opt['data']
    })
    logger.debug(''.join([
        f"original text is: \n{opt['data']}\n",
        f"splitted text is: \n{texts}\n"
    ]))


    # step 2
    # Generate the QA list.
    qa_list = [['q', 'a']]
    zhi_pu_ai_service.init_service({
        'api_key': config.zhipuai_api_key
    })
    for item in texts:
        text = item.replace("\n", "")
        data = zhi_pu_ai_service.generate_qa({
            'text': text
        })
        qa_list.extend(data)

    return qa_list


def _convert_support_type_to_map(supprt_type):
    """Convert support type to map.
    
    support_type: support type list
    example
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
    for item in supprt_type:
        result[item['type']] = 1

    return result