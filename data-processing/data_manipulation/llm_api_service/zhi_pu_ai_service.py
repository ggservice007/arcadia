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
import zhipuai
import traceback

from common import config, log_tag_const


logger = logging.getLogger(__name__)


def init_service(opt={}):
    """Initialize the ZhiPuAI service."""
    zhipuai.api_key = opt['api_key']


def generate_qa(opt={}):
    """Generate the questions and answers."""
    text = opt['text']
    content = """
        我会给你一段文本，它们可能包含多个主题内容，学习它们，并整理学习成果，要求为：
        1. 提出最多 25 个问题。
        2. 给出每个问题的答案。
        3. 答案要详细完整，答案可以包含普通文字、链接、代码、表格、公示、媒体链接等 markdown 元素。
        4. 按格式返回多个问题和答案:

        Q1: 问题。
        A1: 答案。
        Q2:
        A2:
        ……

        我的文本：
    """

    content = content + text
    result = []
    try:
        response = zhipuai.model_api.invoke(
            model="chatglm_6b",
            prompt=[{"role": "user", "content": content}],
            top_p=0.7,
            temperature=0.9,
        )
        if response['success']:
            result = _format_response_to_qa_list(response)
        else:
            logger.error(''.join([
                f"{log_tag_const.ZHI_PU_AI} Cannot access the ZhiPuAI service.\n",
                f"The error is: \n{response['msg']}\n"
            ]))
    except Exception as ex:
        result = []
        logger.error(''.join([
            f"{log_tag_const.ZHI_PU_AI} Cannot access the ZhiPuAI service.\n",
            f"The tracing error is: \n{traceback.format_exc()}\n"
        ]))

    return result


def _format_response_to_qa_list(response):
    """Format the response to the QA list."""
    text = response['data']['choices'][0]['content']

    pattern = re.compile(r'Q\d+:(\s*)(.*?)(\s*)A\d+:(\s*)([\s\S]*?)(?=Q|$)')
    # 移除换行符
    text = text.replace('\\n', '')
    matches = pattern.findall(text)

    result = []
    for match in matches:
        q = match[1]
        a = match[4]
        if q and a:
            result.append([q, a])

    return result
