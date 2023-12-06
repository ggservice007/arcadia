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


import os


def get_file_name(opt={}):
    """Get file name."""
    file_name = opt['file_name']
    handle_name = opt['handle_name']

    file_extension = file_name.split('.')[-1].lower()
    file_name_without_extension = file_name.rsplit('.', 1)[0]

    return file_name_without_extension + '_' + handle_name + '.' + file_extension


def get_temp_file_path():
    """Get temp file path"""
    current_directory = os.getcwd()

    csv_file_path = os.path.join(current_directory, 'file_handle/temp_file/')

    return csv_file_path



def delete_file(file_path):
    """Delete file"""
    os.remove(file_path)
