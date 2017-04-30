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
      version='0.6',
      description="Configurable notifications for trac tickets tied to workflow actions",
      long_description=long_description,
      packages=['workflow_notification'],
      author='Ethan Jucovy',
      author_email='ejucovy@gmail.com',
      url="http://trac-hacks.org/wiki/WorkflowNotificationPlugin",
      license='BSD',
      entry_points = {
        'trac.plugins':
            ['workflow_notification = workflow_notification']
        },
      include_package_data=True,
      zip_safe=False,
      )
