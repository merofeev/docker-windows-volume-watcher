from setuptools import setup, find_packages

setup(name='docker-windows-volume-watcher',
      version='1.0.0',
      packages=find_packages(),
      entry_points={
          'console_scripts': ['docker-volume-watcher=docker_volume_watcher.cli:main'],
          },
      description='A tool to notify Docker contianers about changes in mounts on Windows.',
      author='Mikhail Erofeev',
      author_email=['mikhail@erofeev.pw'],
      url='http://github.com/merofeev/docker-windows-volume-watcher',
      install_requires=[
        'watchdog>=0.8.3',
        'docker>=2.2.1',
        'pypiwin32>=2.2.0; platform_system=="Windows"'
        ],
      license='MIT',
      keywords='Docker volume Windows watch inotify',
  )
