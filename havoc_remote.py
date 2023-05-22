import os
import re
import shutil
import signal
import random
import socket
import pathlib
import requests
import docker
import subprocess
import time as t

class Remote:

    def __init__(self):
        self.args = {}
        self.host_info = None
        self.results = None
        self.commands = {}
        self.share_data = {}
        self.containers = {}
        self.__docker_client= None
    
    @property
    def docker_client(self):
        """Returns a docker client (establishes one automatically if one does not already exist)"""
        if self.__docker_client is None:
            self.__docker_client = docker.from_env()
        return self.__docker_client

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
        if 'get_output' in self.args:
            if 'timeout' not in self.args:
                output = {'outcome': 'failed', 'message': 'a timeout value must be supplied with get_output', 'forward_log': 'False'}
                return output
            get_output = self.args['get_output']
            timeout = self.args['timeout']

        popen_args = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
        if shell:
            popen_args['shell'] = True
        command_id = len(self.commands) + 1
        self.commands[command_id] = {}
        self.commands[command_id]['command'] = command
        try:
            self.commands[command_id]['process'] = subprocess.Popen(command, **popen_args)
            pid = self.commands[command_id]['process'].pid
            self.commands[command_id]['pid'] = pid
            output = {
                'outcome': 'success', 
                'task_execute_command': {
                    'command_id': command_id, 
                    'command': command, 
                    'pid': pid
                },
                'forward_log': 'True'
            }
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_execute_command failed with error: {e}', 'forward_log': 'True'}
            return output
        if get_output:
            signal.alarm(int(timeout))
            try:
                command_output = self.commands[command_id]['process'].communicate()
            except Exception as e:
                output = {'outcome': 'failed', 'message': f'task_execute_command failed with error: {e}', 'forward_log': 'True'}
                return output
            self.commands[command_id]['output'] = command_output
            command_stdout = command_output[0].decode('utf-8')
            command_stderr = command_output[1].decode('utf-8')
            output['task_execute_command']['output'] = {}
            output['task_execute_command']['output']['stdout'] = command_stdout
            output['task_execute_command']['output']['stderr'] = command_stderr
            signal.alarm(0)

        return output

    def task_get_command_output(self):
        required_args = ['command_id', 'timeout']
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
                return output
        command_id = self.args['command_id']
        timeout = self.args['timeout']
        if not self.commands[command_id]:
            output = {
                'outcome': 'failed', 
                'message': f'command_id {command_id} not found in list of previously executed commands', 
                'forward_log': 'False'
            }
            return output
        pid = self.commands[command_id]['pid']
        command = self.commands[command_id]['command']
        output = {
            'outcome': 'success', 
            'task_get_command_output': {
                'command_id': command_id, 
                'command': command, 
                'pid': pid
            }, 
            'forward_log': 'True'
        }

        if 'output' in self.commands[command_id]:
            command_output = self.commands[command_id]['output']
        else:
            signal.alarm(int(timeout))
            try:
                command_output = self.commands[command_id]['process'].communicate()
            except Exception as e:
                output = {'outcome': 'failed', 'message': f'task_get_command_output failed with error: {e}', 'forward_log': 'True'}
                return output
            self.commands[command_id]['output'] = command_output
            
        command_stdout = command_output[0].decode('utf-8')
        command_stderr = command_output[1].decode('utf-8')
        output['task_execute_command']['output'] = {}
        output['task_execute_command']['output']['stdout'] = command_stdout
        output['task_execute_command']['output']['stderr'] = command_stderr

        return output

    def task_kill_command(self):
        if 'command_id' not in self.args:
            output = {'outcome': 'failed', 'message': 'instruct_args must specify command_id', 'forward_log': 'False'}
            return output
        command_id = self.args['command_id']
        if not self.commands[command_id]:
            output = {
                'outcome': 'failed', 
                'message': f'command_id {command_id} not found in list of previously executed commands', 
                'forward_log': 'False'
            }
            return output
        self.commands[command_id]['process'].terminate()
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
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
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
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
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
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
                return output
        
        file_path = self.args['file_path']
        if not os.path.exists(pathlib.Path(file_path)):
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {file_path} does not exist', 'forward_log': 'False'}
            return output
        file_count = int(self.args['file_count'])
        share_name = self.args['share_name']
        try:
            data_volume = int(int(self.args['data_volume']) * 1048576)
            file_size = data_volume/file_count
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output

        word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
        response = requests.get(word_site)
        word_list = response.content.splitlines()
        extensions_list = ['.txt', '.pdf', '.xlsx', '.docx', '.jpg', '.png']
        
        self.share_data[share_name] = {}
        self.share_data[share_name]['file_path'] = str(pathlib.Path(file_path, share_name))
        self.share_data[share_name]['files'] = []
        try:
            os.makedirs(pathlib.Path(file_path, share_name))
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output
        contents = '\0' * int(file_size)
        while file_count != 0:
            file_name = random.choice(word_list).decode() + random.choice(extensions_list)
            path = pathlib.Path(file_path, share_name, file_name)
            with open(path, 'wb+') as f:
                f.write(contents.encode())
            self.share_data[share_name]['files'].append(file_name)
            file_count -= 1
        
        from win32 import win32net
        from win32 import win32security
        shinfo = {}
        shinfo['netname'] = share_name
        shinfo['type'] = win32security.STYPE_DISKTREE
        shinfo['permissions'] = 0
        shinfo['max_uses'] = -1
        shinfo['path'] = str(pathlib.Path(file_path, share_name))
        server = self.host_info[1]

        try:
            win32net.NetShareAdd(server, 2, shinfo)
        except Exception as e:
            shutil.rmtree(pathlib.Path(file_path, share_name))
            output = {'outcome': 'failed', 'message': f'task_create_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output
        
        final_path = str(pathlib.Path(file_path, share_name))
        files = self.share_data[share_name]['files']
        output = {'outcome': 'success', 'task_create_share_with_data': {'file_path': final_path, 'share_name': share_name, 'files': files}, 'forward_log': 'True'}
        return output
    
    def task_delete_share_with_data(self):
        required_args = ['share_name']
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
                return output
    
        share_name = self.args['share_name']
        if share_name not in self.share_data:
            output = {'outcome': 'failed', 'message': f'task_delete_share_with_data failed with error: share does not exist', 'forward_log': 'False'}
            return output
        
        from win32 import win32net
        server = self.host_info[1]
        
        try: 
            win32net.NetShareDel(server, share_name)
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_delete_share_with_data failed with error: {e}', 'forward_log': 'False'}
            return output

        file_path = self.share_data[share_name]['file_path']
        shutil.rmtree(pathlib.Path(file_path))
        
        del self.share_data[share_name]
        output = {'outcome': 'success', 'task_delete_share_with_data': {'share_name': share_name}, 'forward_log': 'True'}
        return output

    def task_list_shares_with_data(self):
        shares_list = []
        if self.share_data:
            for share in self.share_data.keys():
                file_path = self.share_data[share]['file_path']
                files = self.share_data[share]['files']
                share_dict = {
                    'share_name': share,
                    'file_path': file_path,
                    'files': files
                }
                shares_list.append(share_dict)
        output = {'outcome': 'success', 'task_list_shares_with_data': shares_list, 'forward_log': 'True'}
        return output
    
    def task_run_container(self):
        required_args = ['container_name', 'container_image', 'container_ports']
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
                return output
        
        cn = self.args['container_name']
        if cn in self.containers:
            output = {'outcome': 'failed', 'message': f'task_run_container failed with error: container with name {cn} already exists', 'forward_log': 'False'}
            return output
        
        ci = self.args['container_image']
        cp = self.args['container_ports']
        all_ports = False
        if cp == 'all_ports':
            all_ports = True
        cc = None
        if 'container_command' in self.args:
            cc = self.args['container_command']
        
        self.containers[cn] = {}
        self.containers[cn]['container_image'] = ci
        self.containers[cn]['container_ports'] = cp
        container_args = {'name': cn, 'remove': True, 'detach': True}
        if all_ports:
            container_args['network_mode'] = 'host'
        else:
            container_args['ports'] = cp
        if cc:
            container_args['command'] = cc
        
        try:
            self.containers[cn]['container'] = self.docker_client.containers.run(ci, **container_args)
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_run_container failed with error: {e}', 'forward_log': 'False'}
            return output
        container_id = self.containers[cn]['container'].id
        container_dict = {'container_name': cn, 'container_image': ci, 'container_ports': cp, 'container_id': container_id}
        output = {'outcome': 'success', 'task_run_container': container_dict, 'forward_log': 'True'}
        return output
    
    def task_get_container_logs(self):
        required_args = ['container_name']
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
                return output
            
        container_name = self.args['container_name']
        if container_name not in self.containers:
            output = {'outcome': 'failed', 'message': f'task_get_container_logs failed with error: container does not exist', 'forward_log': 'False'}
            return output
        
        try:
            container = self.docker_client.containers.get(container_name)
            container_logs = container.logs().decode()
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_get_container_logs failed with error: {e}', 'forward_log': 'False'}
            return output
        
        output = {'outcome': 'success', 'task_get_container_logs': {'container_name': container_name, 'container_logs': container_logs}, 'forward_log': 'True'}
        return output


    def task_stop_container(self):
        required_args = ['container_name']
        for arg in required_args:
            if arg not in self.args:
                output = {'outcome': 'failed', 'message': f'instruct_args must specify {arg}', 'forward_log': 'False'}
                return output
        
        container_name = self.args['container_name']
        if container_name not in self.containers:
            output = {'outcome': 'failed', 'message': f'task_stop_container failed with error: container does not exist', 'forward_log': 'False'}
            return output
        container = None
        try:
            container = self.docker_client.containers.get(container_name)
        except:
            pass

        try:
            if container:
                container.stop()
            del self.containers[container_name]
        except Exception as e:
            output = {'outcome': 'failed', 'message': f'task_stop_container failed with error: {e}', 'forward_log': 'False'}
            return output
        
        output = {'outcome': 'success', 'task_stop_container': {'container_name': container_name}, 'forward_log': 'True'}
        return output
    
    def task_list_containers(self):
        container_list = []
        if self.containers:
            for container in self.containers.keys():
                c = None
                try:
                    c = self.docker_client.containers.get(container)
                except:
                    pass
                if c:
                    container_id = self.containers[container]['container'].id
                    container_image = self.containers[container]['container_image']
                    container_ports = self.containers[container]['container_ports']
                    container_dict = {
                        'container_name': container, 
                        'container_id': container_id, 
                        'container_image': container_image, 
                        'container_ports': container_ports
                    }
                    container_list.append(container_dict)
        output = {'outcome': 'success', 'task_list_containers': container_list, 'forward_log': 'True'}
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
