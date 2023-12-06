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


from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate



def init_service(opt={}):
    """Initialize the OpenAI service.
    
    opt is a dictionary object. It has the following keys:
    api_key: api key;
    base_url: base url;
    model: model;
    model_type: model type;
    """
    api_key = opt.get('api_key', 'happy')
    base_url = opt.get('base_url', 'http://arcadia-fastchat.172.22.96.167.nip.io/v1')
    model = opt.get('model', 'baichuan2-7b-worker-baichuan-sample-playground')
    model_type = opt.get('model_type', 'bai_chuan_2')
    
    llm = OpenAI(
        openai_api_key=api_key, 
        base_url=base_url,
        model=model
    ) 

    return {
        'llm': llm,
        'model_type': model_type
    } 


def generate_qa(llm, opt={}):
    """Generate the questions and answwers.
    
    llm: llm;
    opt is a dictionary object. It has the following keys:
    text: text;
    model_type: model type;
    model_prompt_template: model prompt template
    """
    default_model_template = """
        {text}
        
        将上述内容提出最多 25 个问题。给出每个问题的答案。每个问题必须有答案。
    """

    model_prompt_template = opt.get('model_prompt_template', default_model_template)   
    prompt = PromptTemplate(template=model_prompt_template, input_variables=["text"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    result = []
    response = llm_chain.run(opt['text'])

    if opt['model_type'] == 'bai_chuan_2':
        result = _get_qa_list_from_response_bai_chuan_2(response)

    return result


def _get_qa_list_from_response_bai_chuan_2(response_text):
    """Get the QA list from the response for BaiChuan2 model.
    
    Notice: There are some problems in the local OpenAI service by BaiChuan2.
    Some time it cannot return the correct question and answer list.
    """
    result = []

    
    return result




