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


from langchain.text_splitter import SpacyTextSplitter


def init_spacy_text_splitter(opt={}):
    """Get a spacy text splitter.
    
    opt is a dictionary object. It has the following keys:
    separator: separator;
    chunk_size: chunk size;
    chunk_overlap: chunk overlap;
    """
    return SpacyTextSplitter(
        separator=opt['separator'],
        pipeline="zh_core_web_sm",
        chunk_size=int(opt['chunk_size']),
        chunk_overlap=int(opt['chunk_overlap'])
    )


def get_splitted_text_by_spacy(spacy_splitter, opt={}):
    """Get the list of the splitted text by spacy.
    
    opt is a dictionary object. It has the following keys:
    data: the data to be splitted;
    """
    return spacy_splitter.split_text(opt['data'])

