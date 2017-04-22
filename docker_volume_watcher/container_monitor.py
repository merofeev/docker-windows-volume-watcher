'''Exports ContainerMonitor to monitor container start/stop events and spawn notifiers.'''

import logging
import re
from datetime import datetime, timedelta
from fnmatch import fnmatch

import docker

from docker_volume_watcher.container_notifier import ContainerNotifier

def docker_bind_to_windows_path(path):
    '''Converts Hyper-V mount path to Windows path (e.g. /C/some-path -> C:/some-path).'''
    expr = re.compile('^/([a-zA-Z])/(.*)$')
    match = re.match(expr, path)
    if not match:
        return None
    return '%s:\\%s' % match.groups()


class ContainerMonitor(object):
    '''Monitors container start/stop events and creates notifiers for mounts matching patterns.'''

    def __init__(self, container_name_pattern, host_dir_pattern):
        self.client = docker.from_env()
        self.container_name_pattern = container_name_pattern
        self.host_dir_pattern = host_dir_pattern
        self.notifiers = {}

    def __handle_event(self, event):
        container_name = event['Actor']['Attributes']['name']
        status = event['status']

        if not fnmatch(container_name, self.container_name_pattern):
            return

        if status == 'start':
            self.watch_container(container_name)
        elif status == 'stop':
            self.unwatch_container(container_name)

    def find_containers(self):
        '''Traverse running containers and spawn notifiers for mounts mattching patterns.'''

        notifiers_count = 0
        for container in self.client.containers.list():
            if fnmatch(container.name, self.container_name_pattern):
                notifiers = self.watch_container(container.name)
                notifiers_count += len(notifiers)

        if notifiers_count == 0:
            logging.warning(
                'No mounts match container name pattern %s and host directory pattern %s',
                self.container_name_pattern, self.host_dir_pattern)

    def watch_container(self, container_name):
        '''Create notifiers for mounts of container_name matching host_dir_pattern.

        Args:
            container_name (str): name of container.

        Returns:
            List of spawned ContainerNotifier-s.
        '''

        container = self.client.containers.get(container_name)
        mounts = container.attrs['Mounts']
        if container not in self.notifiers:
            self.notifiers[container_name] = []
        notifiers = self.notifiers[container_name]

        for mount in mounts:
            if mount['Type'] != 'bind':
                continue
            host_directory = docker_bind_to_windows_path(mount['Source'])
            if not host_directory:
                logging.warning(
                    'Bind of container %s was skipped since it has invalid source path %s',
                    container_name, mount['Source'])
                continue
            if not fnmatch(host_directory, self.host_dir_pattern):
                continue
            notifier = ContainerNotifier(container, host_directory, mount['Destination'])
            notifiers.append(notifier)
            logging.info('Notifier %s created.', notifier)
        return notifiers

    def unwatch_container(self, container_name):
        '''Destroy all notifiers of container_name.'''

        if container_name not in self.notifiers:
            return
        for notifier in self.notifiers[container_name]:
            notifier.stop()
            logging.info('Notifier %s destroyed.', notifier)
        del self.notifiers[container_name]

    def unwatch_all(self):
        '''Destroy all notifiers.'''

        containers = list(self.notifiers)
        for name in containers:
            self.unwatch_container(name)

    def monitor(self):
        '''Start listening and handling of container start/stop events.'''

        delta = timedelta(seconds=2)
        since = datetime.utcnow()
        until = datetime.utcnow() + delta
        filters = {'event': ['start', 'stop'], 'type': 'container'}
        while True:
            for event in self.client.events(since=since, until=until, decode=True, filters=filters):
                self.__handle_event(event)
            since = until
            until = datetime.utcnow() + delta
