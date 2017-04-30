import inspect
import pkg_resources
import sys
from StringIO import StringIO

from genshi.template.text import (NewTextTemplate as TextTemplate,
                                  TemplateSyntaxError)
from trac.admin.api import IAdminCommandProvider, IAdminPanelProvider
from trac.core import *
from trac.config import *
from trac.notification import NotifyEmail
from trac.ticket.api import ITicketChangeListener, ITicketActionController, TicketSystem
from trac.util.text import CRLF
from trac.util.translation import _
from trac.web.chrome import Chrome, ITemplateProvider, add_warning, add_notice

class TicketWorkflowNotifier(Component):
    implements(ITicketChangeListener, ITicketActionController, ITemplateProvider,
               IAdminCommandProvider, IAdminPanelProvider)

    def get_admin_panels(self, req):
        """Return a list of available admin panels.

        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        if 'TICKET_ADMIN' in req.perm('admin', 'ticket/workflow_notification'):
            yield ('ticket', 'Ticket System',
                   "workflow_notification", "Workflow Notifications")

    def render_admin_panel(self, req, category, page, path_info):

        if path_info is None:
            return self.render_admin_panel_list(req)
        return self.render_admin_panel_detail(req, path_info)

    def render_admin_panel_detail(self, req, name):
        section = self.config['ticket-workflow-notifications']
        rule = {}
        rule['condition'] = section.get('%s.condition' % name, None)
        for key in 'body subject recipients'.split():
            val = section.get('%s.%s' % (name, key))
            if key == 'recipients':
                val = [i.strip() for i in val.split(",")]
            rule[key] = val
        rule['actions'] = [i.strip() for i in section.get(name).split(",")]

        data = {
            'rule': rule,
            'name': name,
            }
        if req.method == "GET":
            return ('workflow_notification_rule_admin.html', data)

        for key in 'body subject condition recipients actions'.split():
            if key in ("actions", "recipients"):
                rule[key] = [i.strip() for i in req.args[key].split(",")]
            else:
                rule[key] = req.args[key] # @@TODO fail gracefully if keys are missing
            if key == "actions":
                self.config.set("ticket-workflow-notifications", name, ','.join(rule['actions']))
            else:
                if key == "recipients":
                    self.config.set("ticket-workflow-notifications",
                                    "%s.recipients" % name, ','.join(rule[key]))
                else:
                    self.config.set("ticket-workflow-notifications",
                                    "%s.%s" % (name, key), rule[key])
        errs = StringIO()
        try:
            self.validate(ostream=errs)
        except TemplateSyntaxError:
            errs.seek(0)
            add_warning(req, errs.read())
            self.config.parse_if_needed(force=True)
            return ('workflow_notification_rule_admin.html', data)
        else:
            self.config.save()
            add_notice(req, "Your changes have been saved")
            return req.redirect(req.href("admin/ticket/workflow_notification/%s" % name))

    def render_admin_panel_list(self, req):

        section = self.config['ticket-workflow-notifications']
        notifications = {}

        for name in section:
            if '.' in name:
                continue
            rule = {}
            rule['condition'] = section.get('%s.condition' % name, None)
            for key in 'body subject recipients'.split():
                val = section.get('%s.%s' % (name, key))
                if key == 'recipients':
                    val = [i.strip() for i in val.split(",")]
                rule[key] = val
            rule['actions'] = [i.strip() for i in section.get(name).split(",")]
            notifications[name] = rule

        newrule = {}
        data = {
            'notifications': notifications,
            'newrule': newrule,
            }
        if req.method == "GET":
            return ('workflow_notification_admin.html', data)

        if 'remove' in req.args:
            to_remove = req.args['sel']
            for name in to_remove:
                section.remove(name)
                for key in 'body subject recipients condition'.split():
                    section.remove("%s.%s" % (name, key))

            errs = StringIO()
            try:
                self.validate(ostream=errs)
            except TemplateSyntaxError:
                errs.seek(0)
                add_warning(req, errs.read())
                self.config.parse_if_needed(force=True)
                return ('workflow_notification_admin.html', data)
            else:
                self.config.save()
                add_notice(req, "Deleted %s rules (%s)" % (
                        len(to_remove), ", ".join(to_remove)))
                return req.redirect(
                    req.href("admin", "ticket", "workflow_notification"))

        assert 'add' in req.args #@@TODO error message

        newrule.update({
            'name': req.args.get('name', ''),
            'actions': req.args.get('actions', ''),
            'recipients': req.args.get('recipients', ''),
            'condition': req.args.get('condition', ''),
            'subject': req.args.get('subject', ''),
            'body': req.args.get('body', ''),
            })

        for key in 'name actions recipients subject body'.split():
            if not req.args.get(key, '').strip():
                add_warning(req, "Field '%s' is required." % key)
                return ('workflow_notification_admin.html', data)

        if newrule['name'] in section:
            add_warning(req, "A rule named '%s' already exists.  Please modify or delete it instead." % newrule['name'])
            return ('workflow_notification_admin.html', data)

        self.config.set("ticket-workflow-notifications", newrule['name'], newrule['actions'])
        for key in newrule:
            if key == 'actions' or key == 'name':
                continue
            if not newrule[key].strip():
                continue
            self.config.set("ticket-workflow-notifications", "%s.%s" % (newrule['name'], key),
                            newrule[key])
        errs = StringIO()
        try:
            self.validate(ostream=errs)
        except TemplateSyntaxError:
            errs.seek(0)
            add_warning(req, errs.read())
            self.config.parse_if_needed(force=True)
            return ('workflow_notification_admin.html', data)
        else:
            self.config.save()
            add_notice(req, "Your new notification rule '%s' has been added", newrule['name'])
            return req.redirect(".")


    def get_admin_commands(self):
        return [
            ('workflow_notifications validate', '', 'validate configuration',
             None,
             lambda: self.validate()),
            ]

    def validate(self, ostream=sys.stderr):
        section = self.config['ticket-workflow-notifications']
        for name in section:
            if '.' in name:
                continue
            condition = section.get('%s.condition' % name, None)
            if condition is not None:
                try:
                    TextTemplate(condition)
                except TemplateSyntaxError, e:
                    print >> ostream, "Syntax error in %s.condition" % name
                    print >> ostream, condition
                    raise e
            for key in 'body subject recipients'.split():
                val = section.get('%s.%s' % (name, key))
                try:
                    TextTemplate(val)
                except TemplateSyntaxError, e:
                    print >> ostream, "Syntax error in %s.%s" % (name, key)
                    print >> ostream, val
                    raise e

    def notifications_for_action(self, action):
        section = self.config['ticket-workflow-notifications']
        for key in section:
            if '.' in key:
                continue
            actions_for_key = [i.strip() for i in section.get(key).split(",")]
            if action in actions_for_key:
                yield key
            elif '*' in actions_for_key and not action.startswith('@'):
                yield key

    def build_template_context(self, req, ticket, action):
        ctx = Chrome(self.env).populate_data(None, {'CRLF': CRLF})
        ctx['ticket'] = ticket
        ctx['change'] = {
            'author': req.authname,
            'comment': req.args.get("comment"),
            }
        ctx['action'] = action
        ctx['link'] = self.env.abs_href.ticket(ticket.id)

        if ticket.id:
            old_values = getattr(req, 'ticket_%s_old_values' % ticket.id, {})
        else:
            old_values = {}
        ctx['old_ticket'] = old_values
        return ctx

    def notify(self, req, ticket, name):
        ctx = self.build_template_context(req, ticket, name)
        section = self.config['ticket-workflow-notifications']

        condition = section.get('%s.condition' % name, None)
        if condition is not None:
            condition_value = TextTemplate(condition.replace("\\n", "\n")
                                     ).generate(**ctx).render(encoding=None).strip()
            if condition_value != 'True':
                self.log.debug("Skipping notification %s for ticket %s "
                               "because condition '%s' did not evaluate to True (it evaluated to %s)" % (
                        name, ticket.id if ticket.exists else "(new ticket)",
                        condition, condition_value))
                return False
            else:
                self.log.debug("Sending notification %s for ticket %s "
                               "because condition '%s' did evaluate to True" % (
                        name, ticket.id if ticket.exists else "(new ticket)", condition))
        else:
            self.log.debug("Sending notification %s for ticket %s "
                           "because there was no condition" % (
                    name, ticket.id if ticket.exists else "(new ticket)"))

        body = TextTemplate(section.get('%s.body' % name).replace("\\n", "\n")
                            ).generate(**ctx).render(encoding=None)
        subject = TextTemplate(section.get('%s.subject' % name).replace("\\n", "\n")
                               ).generate(**ctx).render(encoding=None)
        subject = ' '.join(subject.splitlines())
        recipients = TextTemplate(section.get('%s.recipients' % name).replace("\\n", "\n")
                                  ).generate(**ctx).render(encoding=None)
        recipients = [r.strip() for r in recipients.split(",")]

        notifier = WorkflowNotifyEmail(
            self.env, template_name='ticket_notify_workflow_email.txt',
            recipients=recipients, data={'body': body})

        vars = inspect.getargspec(notifier.notify)[0]
        if len(vars) == 3:  # Trac 0.12 and below
            args = [ticket.id, subject]
        elif len(vars) == 4: # Trac 0.13 and up have an additional `author` argument to trac.notification:NotifyEmail.notify
            args = [ticket.id, subject, req.authname]
        else:
            self.log.error("Cannot send notification %s for ticket %s "
                           "because this trac version has an unknown NotifyEmail.notify signature "
                           "%s" % (name, ticket.id if ticket.exists else "(new ticket)", condition,
                                   vars))
            return False
        notifier.notify(*args)

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
        section = self.config['ticket-workflow-notifications']

        hints = []
        for name in self.notifications_for_action(action):
            ctx = self.build_template_context(req, ticket, name)

            subject = TextTemplate(section.get('%s.subject' % name).replace("\\n", "\n")
                                   ).generate(**ctx).render(encoding=None)
            subject = ' '.join(subject.splitlines())
            recipients = TextTemplate(section.get('%s.recipients' % name).replace("\\n", "\n")
                                      ).generate(**ctx).render(encoding=None)
            hints.append(_('An email titled "%(subject)s" will be sent to the following recipients: %(recipients)s', subject=subject, recipients=recipients))

        return None, None, '. '.join(hints) + '.' if hints else None

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
