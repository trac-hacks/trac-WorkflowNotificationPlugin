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

== Configuration == 

Configure one or more notification emails attached to workflow events
using a `ticket-workflow-notifications` section in `trac.ini`.

Within this section, each entry is a notification email that may be
sent out for a ticket.  Here is an example:
{{{
notify_reporter_when_accepted = accept
notify_reporter_when_accepted.body = Hi $ticket.reporter, '$ticket.summary' has been accepted by $change.author. Its status is now $ticket.status.\n\n{% if change.comment %}$change.author said:\n\n$change.comment{% end %}-----\nTicket URL: $link\n$project.name <${project.url or abs_href()}>\n$project.descr
notify_reporter_when_accepted.recipients = $ticket.reporter, trac-admin@hostname.com, trac_user
notify_reporter_when_accepted.subject = '$ticket.summary' is now accepted
}}}

The first line in this example defines the
`notify_reporter_when_accepted` rule. The value in this line defines
one or more workflow actions that will trigger this notification: in
this case, the notification will be triggered when the "accept" action
occurs for any ticket.  (This action is defined by the default
configuration of Trac's built in ticket workflow engine; however, any
action that is defined by the configuration of your installed
ITicketActionControllers may be used.)

We could also define a notification to occur on multiple workflow
actions, using a comma separated list of workflow actions:
{{{
notify_owner_changed = accept, reassign
}}}

Multiple independent notifications can be configured for the same
workflow action; in the above examples, both the
`notify_owner_changed` and the `notify_reported_when_accepted` rules
will be triggered when the "accept" action occurs.

The following lines define the email subject, body, and recipients for
a particular notification.  These are all Genshi Text Templates that
will be rendered with a context that includes the ticket (in its
current state AFTER the workflow action has been applied); the author
and comment of the current change, if any; a link to the ticket as
`$link`; and the project.

All of these must be defined for each notification; the plugin will
raise errors at runtime if a notification is missing any of the
`.subject`, `.body` or `.recipients` definitions.

The `.recipients` definition should be a Genshi template that renders
to a comma separated list of email addresses and/or usernames known to
Trac.  In the above example we combine a dynamic variable based on the
ticket's current state, a username known to Trac, and a hard coded
email address:
{{{
notify_reporter_when_accepted.recipients = $ticket.reporter, trac-admin@hostname.com, trac_user
}}}

