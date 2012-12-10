import inspect
import pkg_resources

from genshi.template.text import NewTextTemplate as TextTemplate
from trac.core import *
from trac.config import *
from trac.notification import NotifyEmail
from trac.ticket.api import ITicketChangeListener, ITicketActionController, TicketSystem
from trac.util.text import CRLF
from trac.web.chrome import Chrome, ITemplateProvider

class TicketWorkflowNotifier(Component):
    implements(ITicketChangeListener, ITicketActionController, ITemplateProvider)

    def notifications_for_action(self, action):
        section = self.config['ticket-workflow-notifications']
        for key in section:
            if '.' in key:
                continue
            actions_for_key = [i.strip() for i in section.get(key).split(",")]
            if action in actions_for_key or '*' in actions_for_key:
                yield key

    def build_template_context(self, req, ticket):
        ctx = Chrome(self.env).populate_data(None, {'CRLF': CRLF})
        ctx['ticket'] = ticket
        ctx['change'] = {
            'author': req.authname,
            'comment': req.args.get("comment"),
            }
        ctx['link'] = self.env.abs_href.ticket(ticket.id)

        if ticket.id:
            old_values = getattr(req, 'ticket_%s_old_values' % ticket.id, {})
        else:
            old_values = {}
        ctx['old_ticket'] = old_values
        return ctx

    def notify(self, req, ticket, name):
        ctx = self.build_template_context(req, ticket)
        section = self.config['ticket-workflow-notifications']

        body = TextTemplate(section.get('%s.body' % name).replace("\\n", "\n")
                            ).generate(**ctx).render(encoding=None)
        subject = TextTemplate(section.get('%s.subject' % name).replace("\\n", "\n")
                               ).generate(**ctx).render(encoding=None)
        subject = ' '.join(subject.splitlines())
        recipients = TextTemplate(section.get('%s.recipients' % name).replace("\\n", "\n")
                                  ).generate(**ctx).render(encoding=None)
        recipients = [r.strip() for r in recipients.split(",")]
        
        WorkflowNotifyEmail(self.env, template_name='ticket_notify_workflow_email.txt',
                            recipients=recipients, data={'body': body}).notify(
            ticket.id, subject, req.authname)
        
    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        system = TicketSystem(self.env)
        for controller in system.action_controllers:
            if controller == self:
                continue
            for action in controller.get_ticket_actions(req, ticket):
                yield action

    def get_all_status(self):
        return []

    def render_ticket_action_control(self, req, ticket, action):
        return None, None, None

    def get_ticket_changes(self, req, ticket, action):
        old_values = {}
        for field in ticket.fields:
            field_name = field['name']
            if field_name in ticket._old:
                # If it's in ticket._old, then it's already been changed
                # by a direct user action before reaching this method;
                # so we should store the value from before the user's change.
                old_values[field_name] = ticket._old[field_name]
            else:
                # If it's not in ticket._old, then the user hasn't directly
                # changed it, but workflow actions might change the value.
                # So we should store the value as it is now, in case it changes.
                old_values[field_name] = ticket[field_name]

        setattr(req, 'ticket_%s_old_values' % ticket.id, old_values)
        return {}

    def apply_action_side_effects(self, req, ticket, action):
        for notification in self.notifications_for_action(action):
            self.log.debug("Notification %s for ticket %s (action: %s)" % (
                    notification, 
                    ticket.id if ticket.exists else "(new ticket)",
                    action))
            self.notify(req, ticket, notification)

    def ticket_deleted(self, ticket):
        pass

    def ticket_created(self, ticket):
        req = None

        for frame, __, ___, ____, _____, ______ in inspect.getouterframes(inspect.currentframe())[1:]:
            if 'req' in frame.f_locals:
                req = frame.f_locals['req']
                break
        if req is None:
            return

        self.apply_action_side_effects(req, ticket, '@created')

    def ticket_changed(self, ticket, comment, author, old_values):
        return 

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('workflow_notification', 'templates')]

class WorkflowNotifyEmail(NotifyEmail):
    _recipients = None

    def __init__(self, env, template_name, recipients, data):
        self.template_name = template_name
        self._recipients = recipients
        NotifyEmail.__init__(self, env)
        self.data.update(data)

    def get_recipients(self, resid):
        return (self._recipients, [])
