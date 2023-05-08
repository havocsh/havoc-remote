import os
import re
import shutil
import random
import socket
import pathlib
import requests
import subprocess
import time as t

class Remote:

    def __init__(self):
        self.args = {}
        self.host_info = None
        self.results = None
        self.exec_process = None
        self.share_data = {}

    def set_args(self, args, public_ip, hostname, local_ip):
        self.args = args
        self.host_info = [public_ip, hostname, local_ip]
        return True

    def task_execute_command(self):
        if 'command' not in self.args:
            output = {'outcome': 'failed', 'message': 'instruct_args must specify command', 'forward_log': 'False'}
            return output
        command = self.args['command']
        shell = None
        if 'shell' in self.args:
            shell = self.args['shell']

        if shell:
            self.exec_process = subprocess.Popen(
                command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            self.exec_process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        if self.exec_process:
            output = {'outcome': 'success', 'task_execute_command': {'command': command, 'pid': self.exec_process.pid}, 'forward_log': 'True'}
        else:
            output = {'outcome': 'failed', 'message': 'command execution failed', 'forward_log': 'True'}
        return output

    def task_get_command_output(self):
        if not self.exec_process:
            output = {'outcome': 'failed', 'message': 'no process is running', 'forward_log': 'False'}
            return output
        process_output = self.exec_process.stdout.read()
        output = {'outcome': 'success', 'task_get_command_output': process_output, 'forward_log': 'True'}
        return output

    def task_kill_command(self):
        if not self.exec_process:
            output = {'outcome': 'failed', 'message': 'no command is running', 'forward_log': 'False'}
            return output
        self.exec_process.terminate()
        output = {'outcome': 'success', 'task_kill_command': 'command killed', 'forward_log': 'True'}
        return output
    
    def task_download_file(self):
        if 'url' not in self.args:
            output = {'outcome': 'failed', 'message': 'instruct_args must specify url', 'forward_log': 'False'}
            return output
        url = self.args['url']
        domain_search = re.search('https?://([^/]+)/', url, re.IGNORECASE)
        domain = None
        if domain_search:
            domain = domain_search.group(1)
        if not domain:
            output = {'outcome': 'failed', 'message': f'invalid url: {url}', 'forward_log': 'False'}
            return output
        if 'file_name' not in self.args:
            output = {'outcome': 'failed', 'message': 'instruct_args must specify file_name', 'forward_log': 'False'}
            return output
        file_name = self.args['file_name']
        resolved_ip = None
        count = 0
        while not resolved_ip and count < 30:
            t.sleep(10)
            try:
                resolved_ip = socket.gethostbyname(domain)
            except:
                pass
            count += 1
        if not resolved_ip:
            output = {'outcome': 'failed', 'message': f'could not resolve domain {domain}', 'forward_log': 'False'}
            return output
        path = pathlib.Path('arsenal', file_name)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        output = {'outcome': 'success', 'task_download_file': {'file_path': 'arsenal', 'file_name': file_name}, 'forward_log': 'True'}
        return output

    def task_create_file(self):
        required_args = ['file_path', 'file_name', 'file_size']
        for k in self.args.keys():
            if k not in required_args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {k}', 'forward_log': 'False'}
                return output
        file_path = self.args['file_path']
        file_name = self.args['file_name']
        file_size = self.args['file_size']
        path = pathlib.Path(file_path, file_name)
        if os.path.exists(file_path):
            with open(path, 'wb+') as f:
                f.write("\0" * file_size)
        else:
            output = {'outcome': 'failed', 'message': f'task_create_file failed with error: {file_path} does not exist', 'forward_log': 'False'}
            return output
        output = {'outcome': 'success', 'task_create_file': {'file_path': file_path, 'file_name': file_name, 'file_size': file_size}, 'forward_log': 'True'}
        return output
    
    def task_delete_file(self):
        required_args = ['file_path', 'file_name']
        for k in self.args.keys():
            if k not in required_args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {k}', 'forward_log': 'False'}
                return output
        file_path = self.args['file_path']
        file_name = self.args['file_name']
        path = pathlib.Path(file_path, file_name)
        if os.path.exists(path):
            os.remove(path)
            output = {'outcome': 'success', 'task_delete_file': {'file_path': file_path, 'file_name': file_name}, 'forward_log': 'True'}
        else:
            output = {'outcome': 'failed', 'message': f'task_delete_file failed with error: {path} does not exist', 'forward_log': 'False'}
        return output
    
    def task_create_share_with_data(self):        
        required_args = ['file_path', 'file_count', 'data_volume', 'share_name']
        for k in self.args.keys():
            if k not in required_args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {k}', 'forward_log': 'False'}
                return output
        
        file_path = self.args['file_path']
        if not os.path.exists(pathlib.Path(file_path)):
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {file_path} does not exist', 'forward_log': 'False'}
            return output
        file_count = self.args['file_count']
        share_name = self.args['share_name']
        try:
            data_volume = int(self.args['data_volume']) * 1048576
            file_size = int(data_volume)/int(file_count)
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output

        word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
        response = requests.get(word_site)
        word_list = response.content.splitlines()
        extensions_list = ['.txt', '.pdf', '.xlsx', '.docx', '.jpg', '.png']
        
        self.share_data[share_name] = {}
        self.share_data[share_name]['file_path'] = pathlib.Path(file_path, share_name)
        self.share_data[share_name]['files'] = []
        try:
            os.makedirs(pathlib.Path(file_path, share_name))
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output
        while file_count != 0:
            file_name = random.choice(word_list).decode() + random.choice(extensions_list)
            path = pathlib.Path(file_path, share_name, file_name)
            with open(path, 'wb+') as f:
                f.write("\0" * int(file_size))
            self.share_data[share_name]['files'].append(file_name)
            file_count =- 1
        
        import win32net
        import win32netcon
        shinfo = {}
        shinfo['netname'] = share_name
        shinfo['type'] = win32netcon.STYPE_DISKTREE
        shinfo['permissions'] = 0
        shinfo['max_uses'] = -1
        shinfo['path'] = pathlib.Path(file_path, share_name)
        server = self.host_info[1]

        try:
            win32net.NetShareAdd(server, 2, shinfo)
        except win32net.error as e:
            for f in self.share_data[share_name]['files']:
                path = pathlib.Path(file_path, share_name, f)
                os.remove(path)
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output
        
        final_path = pathlib.Path(file_path, share_name)
        output = {'outcome': 'success', 'task_create_share_with_data': {'file_path': final_path, 'share_name': share_name, 'files': self.share_data['files']}, 'forward_log': 'True'}
        return output
    
    def task_delete_share_with_data(self):
        required_args = ['share_name']
        for k in self.args.keys():
            if k not in required_args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {k}', 'forward_log': 'False'}
                return output
    
        share_name = self.args['share_name']
        if share_name not in self.share_data:
            output = {'outcome': 'failed', 'message': f'task_delete_share_with_data failed with error: share does not exist', 'forward_log': 'False'}
            return output
        
        import win32net
        server = self.host_info[1]
        
        try: 
            win32net.NetShareDel(server, share_name)
        except win32net.error as e:
            output = {'outcome': 'failed', 'message': f'task_delete_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output

        file_path = self.share_data[share_name]['file_path']
        shutil.rmtree(pathlib.Path(file_path))
        
        del self.share_data[share_name]
        output = {'outcome': 'success', 'task_delete_share_with_data': {'share_name': share_name}, 'forward_log': 'True'}
        return output

    def echo(self):
        match = {
            'foo': 'bar',
            'bar': 'baz',
            'ping': 'pong',
            'and then': 'no more and then',
            'pen testing is dead': 'long live pen testing',
            'never gonna give you up': 'never gonna let you down, never gonna run around and desert you',
            'never gonna make you cry': 'never gonna say goodbye, never gonna tell a lie and hurt you'
        }

        if 'echo' in self.args:
            echo = self.args['echo']
            if echo in match:
                output = {'outcome': 'success', 'echo': match[echo], 'forward_log': 'False'}
            else:
                output = {'outcome': 'success', 'echo': 'OK', 'forward_log': 'False'}
        else:
            output = {'outcome': 'success', 'echo': 'OK', 'forward_log': 'False'}

        return output
