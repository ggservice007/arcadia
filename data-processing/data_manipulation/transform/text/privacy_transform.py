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
import re
import traceback

from common import log_tag_const, special_characters


logger = logging.getLogger(__name__)


def remove_email(opt={}):
    """Replace email info with the user defined string.
    
    opt is a dictionary object. It has the following keys:
    text: text;
    replace_string: the text is used to replace the email info;
    """
    text = opt['text']
    replace_string = opt.get('replace_string', 'T:EMAIL')

    try:
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
   
        matches = re.findall(pattern, text)
        clean_text = re.sub(pattern, replace_string, text)
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
            f"{log_tag_const.CLEAN_TRANSFORM} Execute removing email.\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))
        return {
            'status': 400,
            'message': str(ex),
            'data': traceback.format_exc()
        }