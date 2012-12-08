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

== Installation ==

Install the plugin's source code:
{{{
$ easy_install trac-WorkflowNotificationPlugin
}}}

Enable its components in trac.ini:
{{{
[components]
workflow_notification.* = enabled
}}}

Add its component to your list of workflow providers, after all other
workflow providers; for example:
{{{
[ticket]
workflow = ConfigurableTicketWorkflow, TicketWorkflowNotifier
}}}

Now you just need to configure some notifications; see below for
details and examples.

