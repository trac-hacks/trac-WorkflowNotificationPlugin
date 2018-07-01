from setuptools import setup

try:
    long_description = open("README.txt").read()
except:
    long_description = ''
try:
    long_description += open("CHANGES.txt").read()
except:
    pass

setup(name='trac-WorkflowNotificationPlugin',
      version='0.7',
      description="Configurable notifications for trac tickets tied to workflow actions",
      long_description=long_description,
      packages=['workflow_notification'],
      package_data = {
        'workflow_notification': [
            'templates/*.html',
            'templates/*.txt',
        ],
      },
      author='Ethan Jucovy',
      author_email='ejucovy@gmail.com',
      url="https://trac-hacks.org/wiki/WorkflowNotificationPlugin",
      license='BSD',
      entry_points = {
        'trac.plugins':
            ['workflow_notification = workflow_notification']
        },
      zip_safe=False,
      )
