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
import opencc
import re
from selectolax.parser import HTMLParser
import traceback

from common import log_tag_const, special_characters


logger = logging.getLogger(__name__)


def remove_invisible_characters(opt={}):
    """remove invisible characters.
    
    opt is a dictionary object. It has the following keys:
    text: text;

    usage
    input:
    “一户一表、水表出户、抄表到户”是指一个家庭用户安装一个计量水表，计量水表安装在住宅的公共部位，供水企业抄表到户，按户计量收费。
    output:
    “一户一表、水表出户、抄表到户”是指一个家庭用户安装一个计量水表，计量水表安装在住宅的公共部位，供水企业抄表到户，按户计量收费。
    """
    try:
        text = opt['text']
        pattern = r'[\x00-\x1F\x7F-\x9F\xAD\r\n\t\b\x0B\x1C\x1D\x1E]'

        matches = re.findall(pattern, text)
        clean_text = re.sub(pattern, '', text)
        return {
            'status': 200,
            'message': '',
            'data': {
                'found': len(matches),
                'text': clean_text
            }
        }
    except Exception as ex:
        logger.error(''.join([
            f"{log_tag_const.CLEAN_TRANSFORM} Execute removing invisible characters failed\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))
        return {
            'status': 400,
            'message': str(ex),
            'data': traceback.format_exc()
        }


def space_standardization(opt={}):
    """space standardization.
    
    opt is a dictionary object. It has the following keys:
    text: text;
    """
    try:
        text = opt['text']
        clean_text = ''.join([
            char if char not in special_characters.VARIOUS_WHITESPACES else ' ' for char in text
        ])
        return {
            'status': 200,
            'message': '',
            'data': {
                'found': 0,
                'text': clean_text
            }
        }
    except Exception as ex:
        logger.error(''.join([
            f"{log_tag_const.CLEAN_TRANSFORM} Executing space standardization failed.\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))
        return {
            'status': 400,
            'message': str(ex),
            'data': traceback.format_exc()
        }


def traditional_to_simplified(opt={}):
    """Traditional Chinese to Simplified Chinese.
    
    opt is a dictionary object. It has the following keys:
    text: text;
    """
    text = opt['text']

    try:
        clean_text = opencc.OpenCC('t2s').convert(text)

        return {
            'status': 200,
            'message': '',
            'data': clean_text
        }
    except Exception as ex:
        error = str(ex)
        logger.error(''.join([
            f"{log_tag_const.CLEAN_TRANSFORM} Executing Traditional Chinese to Simplified Chinese failed\n",
            f"\nThe error is: \n{error}\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))

        return {
            'status': 400,
            'message': error,
            'data': traceback.format_exc()
        }


def remove_html_tag(opt={}):
    """clean html code in text samples.
    
    opt is a dictionary object. It has the following keys:
    text: text;
    """
    text = opt['text']

    try:
        text = text.replace('<li>', '\n*')
        text = text.replace('</li>', '')
        text = text.replace('<ol>', '\n*')
        text = text.replace('</ol>', '')
        parser = HTMLParser(text)

        clean_text = parser.text()

        return {
            'status': 200,
            'message': '',
            'data': clean_text
        }
    except Exception as ex:
        error = str(ex)
        logger.error(''.join([
            f"{log_tag_const.CLEAN_TRANSFORM} Executing clean html code in text samples failed\n",
            f"\nThe error is: \n{error}\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))

        return {
            'status': 400,
            'message': error,
            'data': traceback.format_exc()
        }


def remove_emojis(opt={}):
    """remove emojis.
    
    opt is a dictionary object. It has the following keys:
    text: text;
    """
    text = opt['text']

    try:
        clean_text = ''.join([
            char if char not in special_characters.EMOJI else '' for char in text
        ])
        return {
            'status': 200,
            'message': '',
            'data': clean_text
        }

    except Exception as ex:
        error = str(ex)
        logger.error(''.join([
            f"{log_tag_const.CLEAN_TRANSFORM} Executing remove emojis failed\n",
            f"\nThe error is: \n{error}\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))

        return {
            'status': 400,
            'message': error,
            'data': traceback.format_exc()
        }
