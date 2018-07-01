# Description

WorkflowNotificationPlugin enables flexible configuration of email
notifications tied to ticket workflow changes.

Administrators can configure any number of distinct email
notifications to be sent out when a workflow operation occurs on a
ticket. Each email notification is specifically attached to one or
more workflow operations, so (for example) separate emails can be sent
out when a ticket is accepted, reassigned, resolved, reopened, or
marked "in QA". 

Each email notification's subject, body, and recipients are fully
configurable by administrators, as Genshi templates which have access
to the ticket's data, the comment (if any) that was left on the
ticket, and the author of the change. Therefore notifications can be
very flexible: some notifications can be sent to the ticket's
reporter, others to its owner or CC list, others to the current
updater, and others to hard-coded lists of users.

The notification emails sent by this plugin respect trac's ALWAYS_CC
and ALWAYS_BCC settings.

The notification emails sent by this plugin are orthogonal to trac's
ALWAYS_NOTIFY_UPDATER, ALWAYS_NOTIFY_OWNER, and ALWAYS_NOTIFY_REPORTER
settings; Trac's built-in email notifications will be sent according
to those settings, independent of this plugin's emails.

For docs on installation, configuration, and examples, please refer to
https://trac-hacks.org/wiki/WorkflowNotificationPlugin

# Release Steps

1. Edit version in `setup.py`, and set `tag_build = ` in `setup.cfg`.
2. Tag the release:

    ```
    git tag <version>
    git push --tags
    ```

3. Build the distributables:

    ```
    rm -r build dist
    python setup.py sdist bdist_wheel
    ```

4. Upload to pypi:

    ```
    twine upload dist/*.tag.gz dist/*.whl`
    ```
