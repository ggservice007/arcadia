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


from pypdf import PdfReader


def get_content(opt={}):
    """Get the content from a pdf file.
    
    opt is a dictionary object. It has the following keys:
    file_path: file path;
    """
    reader = PdfReader(opt["file_path"])
    content = ""

    for page in reader.pages:
        content += page.extract_text()

    return content 


