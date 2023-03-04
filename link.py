#!/usr/bin/python3

import os
import sys
import atexit
import signal
import socket
import pathlib
import requests
from configparser import ConfigParser
from datetime import datetime, timezone
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred
import havoc

# Havoc imports
import havoc_remote


class Remote:

    def __init__(self, api_key, secret, api_domain_name, api_region):
        self.api_key = api_key
        self.secret = secret
        self.api_domain_name = api_domain_name
        self.api_region = api_region


def sleep(delay):
    d = Deferred()
    reactor.callLater(delay, d.callback, None)
    return d


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_commands_http(rt, task_name, command_list):
    commands_response = None
    h = havoc.Connect(rt.api_region, rt.api_domain_name, rt.api_key, rt.secret, api_version=1)
    try:
        commands_response = h.get_commands(task_name)
    except Exception as err:
        print(f'get_commands_http failed for task {task_name} with error {err}')

    if commands_response and 'commands' in commands_response:
        for command in commands_response['commands']:
            command_list.append(command)


def post_response_http(rt, results):
    h = havoc.Connect(rt.api_region, rt.api_domain_name, rt.api_key, rt.secret, api_version=1)
    try:
        h.post_response(results)
    except Exception as err:
        print(f'post_response_http failed for results {results} with error {err}')


def sync_workspace_http(rt, sync_direction):
    sync_workspace_response = None
    h = havoc.Connect(rt.api_region, rt.api_domain_name, rt.api_key, rt.secret, api_version=1)
    try:
        sync_workspace_response = h.sync_workspace(sync_direction, '/opt/havoc/shared')
    except Exception as err:
        print(f'sync_workspace_http failed with error {err}')
    return sync_workspace_response


def file_transfer_http(rt, sync_direction, file_name):
    success = False
    file_transfer_response = None
    h = havoc.Connect(rt.api_region, rt.api_domain_name, rt.api_key, rt.secret, api_version=1)
    if sync_direction == 'download_from_workspace':
        try:
            file_transfer_response = h.get_file(file_name)
        except Exception as err:
            print(f'file_transfer_http failed for direction {sync_direction}, file_name {file_name} with error {err}')
        if file_transfer_response and 'file_contents' in file_transfer_response:
            with open(f'/opt/havoc/share/{file_name}', 'wb') as w:
                w.write(file_transfer_response['file_contents'])
            success = True
        else:
            success = False
    if sync_direction == 'upload_to_workspace':
        try:
            with open (f'opt/havoc/shared/{file_name}', 'rb') as raw_file:
                h.create_file(file_name, raw_file.read())
            success = True
        except Exception as err:
            print(f'file_transfer_http failed for direction {sync_direction}, file_name {file_name} with error {err}')
            success = False
    return success


def send_response(rt, task_response, forward_log, user_id, task_name, task_context, task_type, task_version,
                  instruct_user_id, instruct_instance, instruct_command, instruct_args, public_ip, local_ip, end_time):
    current_time = datetime.now(timezone.utc)
    stime = str(int(datetime.timestamp(current_time)))
    output = {
        'instruct_command_output': task_response, 'user_id': user_id, 'task_name': task_name,
        'task_context': task_context, 'task_type': task_type, 'task_version': task_version,
        'instruct_user_id': instruct_user_id, 'instruct_instance': instruct_instance, 'instruct_command': instruct_command,
        'instruct_args': instruct_args, 'public_ip': public_ip, 'local_ip': local_ip, 'end_time': end_time,
        'forward_log': forward_log, 'timestamp': stime
    }
    post_response_http(rt, output)


@inlineCallbacks
def action(user_id, task_type, task_version, task_commands, task_name, task_context, rt, end_time, command_list,
           public_ip, hostname, local_ip):
    
    def exit_handler():
        send_response(rt, {'outcome': 'success', 'status': 'terminating'}, 'True', user_id, task_name,
                      task_context, task_type, task_version, instruct_user_id, 'None', 'terminate',
                      {'no_args': 'True'}, public_ip, local_ip, end_time)
        log.msg('remote_operator task exiting')

    atexit.register(exit_handler)
    local_instruct_instance = {}

    while True:
        def sortFunc(e):
            return e['timestamp']

        command_list.sort(key=sortFunc)
        for c in command_list:
            instruct_user_id = c['instruct_user_id']
            instruct_instance = c['instruct_instance']
            instruct_command = c['instruct_command']
            instruct_args = c['instruct_args']
            if instruct_command == 'Initialize' or instruct_command == 'sync_from_workspace':
                file_list = sync_workspace_http(rt, 'sync_from_workspace')
                if instruct_command == 'Initialize':
                    response_kv = ['status', 'ready']
                else:
                    response_kv = ['outcome', 'success']
                send_response(rt, {response_kv[0]: response_kv[1], 'local_directory_contents': file_list}, 'True',
                            user_id, task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                            instruct_command, instruct_args, public_ip, local_ip, end_time)
            elif instruct_command == 'ls':
                file_list = []
                for root, subdirs, files in os.walk('/opt/havoc/shared'):
                    for filename in files:
                        file_list.append(filename)
                send_response(rt, {'outcome': 'success', 'local_directory_contents': file_list}, 'False',
                            user_id, task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                            instruct_command, instruct_args, public_ip, local_ip, end_time)
            elif instruct_command == 'del':
                if 'file_name' in instruct_args:
                    file_name = instruct_args['file_name']
                    path = pathlib.Path(f'/opt/havoc/shared/{file_name}')
                    if path.is_file():
                        os.remove(path)
                        send_response(rt, {'outcome': 'success'}, 'True', user_id, task_name, task_context, task_type,
                                    task_version, instruct_user_id, instruct_instance, instruct_command, instruct_args,
                                    public_ip, local_ip, end_time)
                    else:
                        send_response(rt, {'outcome': 'failed', 'message': 'File not found'}, 'False', user_id,
                                    task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                                    instruct_command, instruct_args, public_ip, local_ip, end_time)
                else:
                    send_response(rt, {'outcome': 'failed', 'message': 'Missing file_name'}, 'False',
                                user_id, task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                                instruct_command, instruct_args, public_ip, local_ip, end_time)
            elif instruct_command == 'sync_to_workspace':
                file_list = sync_workspace_http(rt, 'sync_to_workspace')
                send_response(rt, {'outcome': 'success', 'local_directory_contents': file_list}, 'False', user_id,
                            task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance, instruct_command,
                            instruct_args, public_ip, local_ip, end_time)
            elif instruct_command == 'upload_to_workspace':
                if 'file_name' in instruct_args:
                    file_name = instruct_args['file_name']
                    path = pathlib.Path(f'/opt/havoc/shared/{file_name}')
                    if path.is_file():
                        file_transfer_http(rt, 'upload_to_workspace', file_name)
                        send_response(rt, {'outcome': 'success'}, 'True', user_id, task_name, task_context, task_type,
                                    task_version, instruct_user_id, instruct_instance, instruct_command, instruct_args,
                                    public_ip, local_ip, end_time)
                    else:
                        send_response(rt, {'outcome': 'failed', 'message': 'File not found'}, 'False', user_id,
                                    task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                                    instruct_command, instruct_args, public_ip, local_ip, end_time)
                else:
                    send_response(rt, {'outcome': 'failed', 'message': 'Missing file_name'}, 'False',
                                user_id, task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                                instruct_command, instruct_args, public_ip, local_ip, end_time)
            elif instruct_command == 'download_from_workspace':
                if 'file_name' in instruct_args:
                    file_name = instruct_args['file_name']
                    file_not_found = False
                    file_download = file_transfer_http(rt,'download_from_workspace', file_name)
                    if not file_download:
                        file_not_found = True
                    if file_not_found:
                        send_response(rt, {'outcome': 'failed', 'message': 'File not found'}, 'False', user_id,
                                    task_name, task_context, task_type, task_version, instruct_user_id, instruct_instance,
                                    instruct_command, instruct_args, public_ip, local_ip, end_time)
                    else:
                        send_response(rt, {'outcome': 'success'}, 'True', user_id, task_name, task_context, task_type,
                                    task_version, instruct_user_id, instruct_instance, instruct_command, instruct_args,
                                    public_ip, local_ip, end_time)
                else:
                    send_response(rt, {'outcome': 'failed', 'message': 'Missing file_name'}, 'False', user_id, task_name,
                                task_context, task_type, task_version, instruct_user_id, instruct_instance, instruct_command,
                                instruct_args, public_ip, local_ip, end_time)
            elif instruct_command == 'terminate':
                os.kill(os.getpid(), signal.CTRL_BREAK_EVENT)
            else:
                if instruct_instance not in local_instruct_instance:
                    local_instruct_instance[instruct_instance] = havoc_remote.Remote()
                if instruct_command in task_commands:
                    local_instruct_instance[instruct_instance].set_args(instruct_args, public_ip, hostname,
                                                                        local_ip)
                    method = getattr(local_instruct_instance[instruct_instance], instruct_command)
                    call_method = method()
                else:
                    call_method = {
                        'outcome': 'failed',
                        'message': f'Invalid instruct_command: {instruct_command}',
                        'forward_log': 'False'
                    }

                forward_log = call_method['forward_log']
                del call_method['forward_log']
                send_response(rt, call_method, forward_log, user_id, task_name, task_context, task_type,
                            task_version, instruct_user_id, instruct_instance, instruct_command, instruct_args, public_ip,
                            local_ip, end_time)
            command_list.remove(c)
        yield sleep(5)


@inlineCallbacks
def get_command_obj(task_name, rt, command_list):
    while True:
        yield sleep(60)
        get_commands_http(rt, task_name, command_list)


def main():

    # Setup vars
    config = ConfigParser()
    config.read('link.ini')
    task_name = config.get('task', 'task_name')
    task_context = config.get('task', 'task_context')
    task_type = config.get('task', 'task_type')
    task_version = config.get('task', 'task_version')
    task_commands = config.get('task', 'task_commands').split(',')
    user_id = config.get('settings', 'user_id')
    api_region = config.get('settings', 'api_region')
    api_domain_name = config.get('settings', 'api_domain_name')
    api_key = config.get('settings', 'api_key')
    secret = config.get('settings', 'secret')
    local_ip = [get_ip()]
    public_ip = None
    end_time = 'None'
    
    log.startLogging(sys.stdout)
    log.msg(
        f'remote_operator task starting - task_name: {task_name}, task_context: {task_context}, '
        f'task_version {task_version}, api_region: {api_region}, api_domain_name: {api_domain_name}, '
        f'user_id: {user_id}, api_key: {api_key}, local_ip: {local_ip}, public_ip: {public_ip}'
    )
    
    var_assignments = {
        'task_name': task_name,
        'task_context': task_context,
        'task_type': task_type,
        'task_version': task_version,
        'task_commands': task_commands,
        'user_id': user_id,
        'api_region': api_region,
        'api_domain_name': api_domain_name,
        'api_key': api_key,
        'secret': secret
    }
            
    for k, v in var_assignments.items():
        if not v:
            print(f'Error: value for {k} in link.ini file cannot be empty')
            os.kill(os.getpid(), 9)

    # Instantiate Remote to serve key_pair as a property
    rt = Remote(api_key, secret, api_domain_name, api_region)

    # Get public IP
    try:
        r = requests.get('http://checkip.amazonaws.com/', timeout=10)
        public_ip = r.text.rstrip()
    except requests.ConnectionError:
        print('Public IP check failed. Exiting...')
        os.kill(os.getpid(), 9)
    hostname = socket.gethostname()

    # Register as a remote task
    try:
        h = havoc.Connect(rt.api_region, rt.api_domain_name, rt.api_key, rt.secret, api_version=1)
        h.register_task(task_name, task_context, task_type, task_version, public_ip, local_ip)
    except Exception as e:
        print(f'Remote task registration failed with error:\n{e}\nExiting...')
        os.kill(os.getpid(), 9)

    # Setup coroutine resources
    command_list = []

    # Setup coroutines
    get_command_obj(task_name, rt, command_list)
    action(user_id, task_type, task_version, task_commands, task_name, task_context, rt, end_time, command_list,
           public_ip, hostname, local_ip)


if __name__ == "__main__":
    reactor.callWhenRunning(main)
    reactor.run()