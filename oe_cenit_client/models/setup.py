#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  connection.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import logging

from openerp import models, fields, api
from openerp.addons.oe_cenit_client import cenit_api  # @UnresolvedImport

from datetime import datetime


_logger = logging.getLogger(__name__)


class CenitConnection (cenit_api.CenitApi, models.Model):
    _name = 'cenit.connection'
    cenit_model = 'connection'
    cenit_models = 'connections'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    url = fields.Char('URL', required=True)

    key = fields.Char('Key', readonly=True)
    token = fields.Char('Token', readonly=True)

    url_parameters = fields.One2many(
        'cenit.parameter',
        'conn_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'conn_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'conn_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name,
            'url': self.url,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})

        headers = []
        for header in self.header_parameters:
            headers.append({
                'key': header.key,
                'value': header.value
            })
        vals.update({'headers': headers})

        template = []
        for tpl in self.template_parameters:
            template.append({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update({'template_parameters': template})

        return vals

    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],
                }

        return update

    @api.one
    def _get_conn_data(self):
        path = "/api/v1/connection/%s" % self.cenitID

        rc = self.get(path)

        _logger.info(rc)
        vals = {
            'key': rc['connection']['number'],
            'token': rc['connection']['token'],
        }
        self.with_context(noPush=True).write(vals)
        return

    @api.model
    def create(self, vals):
        _id = super(CenitConnection, self).create(vals)
        obj = self.browse(_id)

        if obj.cenitID:
            obj._get_conn_data()

        return _id


class CenitConnectionRole (cenit_api.CenitApi, models.Model):
    _name = 'cenit.connection.role'
    cenit_model = 'connection_role'
    cenit_models = 'connection_roles'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)

    connections = fields.Many2many(
        'cenit.connection',
        string='Connections'
    )

    webhooks = fields.Many2many(
        'cenit.webhook',
        string='Webhooks'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []

        connections = []
        for conn in self.connections:
            connections.append(conn._get_values())

        vals.update({
            'connections': connections
        })
        _reset.append('connections')

        webhooks = []
        for hook in self.webhooks:
            webhooks.append(hook._get_values())

        vals.update({
            'webhooks': webhooks
        })
        _reset.append('webhooks')

        vals.update({
            '_reset': _reset
        })

        return vals


class CenitParameter (models.Model):
    _name = 'cenit.parameter'

    key = fields.Char('Key', required=True)
    value = fields.Char('Value', required=True)

    conn_url_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    conn_header_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    conn_template_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    hook_url_id = fields.Many2one(
        'cenit.webhook',
        string='Webhook'
    )

    hook_header_id = fields.Many2one(
        'cenit.webhook',
        string='Webhook'
    )

    hook_template_id = fields.Many2one(
        'cenit.webhook',
        string='Webhook'
    )


class CenitWebhook (cenit_api.CenitApi, models.Model):
    _name = 'cenit.webhook'
    cenit_model = 'webhook'
    cenit_models = 'webhooks'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    path = fields.Char('Path', required=True)
    purpose = fields.Selection(
        [
            ('send', 'Send'),
            ('receive', 'Receive')
        ],
        'Purpose', default='send', required=True
    )
    method = fields.Selection(
        [
            ('get', 'HTTP GET'),
            ('post', 'HTTP POST'),
            ('put', 'HTTP PUT'),
            ('delete', 'HTTP DELETE'),
        ],
        'Method', default='post', required=True
    )

    url_parameters = fields.One2many(
        'cenit.parameter',
        'hook_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'hook_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'hook_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name,
            'path': self.path,
            'purpose': self.purpose,
            'method': self.method,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})

        headers = []
        for header in self.header_parameters:
            headers.append({
                'key': header.key,
                'value': header.value
            })
        vals.update({'headers': headers})

        template = []
        for tpl in self.template_parameters:
            template.append({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update({'template_parameters': template})

        return vals


class CenitFlow (cenit_api.CenitApi, models.Model):

    def _get_translators(self, format_=None, dir_=None):
        path = "/api/v1/translator"

        rc = self.get(path)

        if not isinstance(rc, list):
            rc = [rc]

        values = []

        for item in rc:
            it = item.get("translator")
            if format_ and (it.get('mime_type', '') != format_):
                continue
            if dir_ and (it.get('type', '') != dir_):
                continue
            values.append((it.get('id'), it.get('name')))

        return values

    _name = "cenit.flow"

    cenit_model = 'flow'
    cenit_models = 'flows'

    cenitID = fields.Char('Cenit ID')
    event_cenitID = fields.Char('Cenit Event ID')

    name = fields.Char('Name', size=64, required=True, unique=True)
    execution = fields.Selection(
        [
            # ('only_manual', 'Only Manual'),
            # ('interval', 'Interval'),
            ('on_create', 'On Create'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Create & Update')
        ],
        'Execution', default='on_create_or_write', required=True
    )
    # cron = fields.Many2one('ir.cron', 'Cron rules')

    format_ = fields.Selection(
        [
            ('application/json', 'JSON'),
            ('application/EDI-X12', 'EDI')
        ],
        'Format', default='application/json', required=True
    )
    local = fields.Boolean('Bypass Cenit', default=False)
    cenit_translator = fields.Selection(
        _get_translators, string="Translator"
    )

    data_type = fields.Many2one(
        'cenit.data_type', 'Source data type', required=True
    )
    scope = fields.Selection(
        [
            ('Event', 'Event source'),
            ('All', 'All sources'),
        ],
        'Source scope', default='Event', required=True
    )

    connection_role = fields.Many2one(
        'cenit.connection.role', 'Connection role', required=True
    )
    webhook = fields.Many2one(
        'cenit.webhook', 'Webhook', required=True
    )

    cenit_response_translator = fields.Selection(
        _get_translators, string="Response translator"
    )
    response_data_type = fields.Many2one(
        'cenit.data_type', 'Response data type'
    )

    base_action_rule = fields.Many2one('base.action.rule', 'Action Rule')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name,
            'active': True,
            'discard_events': False,
            'data_type_scope': self.scope,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        if self.execution not in ('only_manual', 'interval'):
            cr = '{"created_at":{"0":{"o":"_not_null","v":["","",""]}}}'
            wr = '{"updated_at":{"0":{"o":"_presence_change","v":["","",""]}}}'
            cr_wr = '{"updated_at":{"0":{"o":"_change","v":["","",""]}}}'
            event = {
                '_type': "Setup::Observer",
                'name': "%s::%s > %s @ %s" % (
                    self.data_type.library.name,
                    self.data_type.name,
                    self.execution,
                    datetime.now().ctime()
                ),
                'data_type': {'id': self.data_type.datatype_cenitID},
                'triggers': {
                    'on_create': cr,
                    'on_write': wr,
                    'on_create_or_write': cr_wr,
                }[self.execution]
            }
            if self.event_cenitID:
                event.update({'id': self.event_cenitID})

            vals.update({
                'event': event
            })

        if self.cenit_translator:
            vals.update({
                'translator': {
                    'id': self.cenit_translator
                }
            })

        if self.data_type.datatype_cenitID:
            vals.update({
                'custom_data_type': {
                    'id': self.data_type.datatype_cenitID
                }
            })

        if self.connection_role:
            vals.update({
                'connection_role': {
                    'id': self.connection_role.cenitID
                }
            })

        if self.webhook:
            vals.update({
                'webhook': {
                    'id': self.webhook.cenitID
                }
            })

        return vals

    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],
                    # 'event_cenitID': v[0] ['event_id']['id']
                }

        return update

    def on_connection_role_changed(self, cr, uid, ids, role_id, context=None):
        role = self.pool.get("cenit.connection.role").browse(
            cr, uid, role_id, context=context
        )
        hook_ids = [x.id for x in role.webhooks]
        domain = {"webhook": [('id', 'in', hook_ids)]}
        rc = {'value': {'webhook': ""}, "domain": domain}

        return rc

    @api.onchange('webhook', 'format_')
    def on_webhook_format_changed(self):
        dir_ = {
            'send': 'Export',
            'receive': 'Import',
        }.get(self.webhook.purpose, '')
        values = self._get_translators(self.format_, dir_)
        self._columns['cenit_translator'].selection = values
#         #~ self.cenit_translator = values[0][0]
#         #~ if self.cenit_translator:
#             #~ self.cenit_translator.selection = values
#
#     #~ method = fields.Selection (
#         #~ [
#             #~ ('http_post', 'HTTP POST'),
#             #~ ('local_post', 'LOCAL POST'),
#             #~ ('file_post', 'FILE POST')
#         #~ ], 'Method', default='http_post'
#     #~ )
# #~
#     #~ base_action_rule = fields.Many2one (
#         #~ 'base.action.rule', 'Action Rule'
#     #~ )
#     #~ ir_cron = fields.Many2one (
#         #~ 'ir.cron', 'Action Cron'
#     #~ )
# #~

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
#        context.update({'local': vals['local']})

        obj_id = super(CenitFlow, self).create(cr, uid, vals, context)

        hook = self.pool.get('cenit.webhook').browse(
            cr, uid, vals['webhook'], context=context
        )
        purpose = hook.purpose

        method = 'set_%s_execution' % (purpose, )
        getattr(self, method)(cr, uid, [obj_id], context)

        return obj_id

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
#        context.update({'local': vals['local']})

        res = super(CenitFlow, self).write(cr, uid, ids, vals, context)

        if vals.get('execution', False):
            for obj in self.browse(cr, uid, ids):
                method = 'set_%s_execution' % obj.webhook.purpose
                getattr(self, method)(cr, uid, [obj.id], context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (long, int)):
            ids = [ids]

        for id_ in ids:
            obj = self.browse(cr, uid, id_, context=context)
            if obj.base_action_rule:
                obj.base_action_rule.unlink()

        return super(CenitFlow, self).unlink(cr, uid, ids, context)

    def find(self, cr, uid, model, purpose, context=None):
        domain = [('data_type.cenit_root', '=', model),
                  ('webhook.purpose', '=', purpose)]
        _logger.info ("\n\nSearching with Domain: %s\n", domain)
        obj_ids = self.search(cr, uid, domain, context=context)
        _logger.info ("\n\nGot: %s\n", obj_ids)
        return obj_ids and self.browse(cr, uid, obj_ids[0]) or False

    def set_receive_execution(self, cr, uid, ids, context=None):
        pass
#         for obj in self.browse(cr, uid, ids):
#             if not obj.local:
#                 flow_reference = self.pool.get('cenit.flow.reference')
#                 try:
#                     flow_reference.set_flow_in_cenit(cr, uid, obj, context)
#                 except:
#                     pass

    def receive(self, cr, uid, model, data, context=None):
        res = False
        context = context or {}
        obj = self.find(cr, uid, model.lower(), 'receive', context)
        _logger.info ("\n\nReceiving %s with %s\n", model, data)
        if obj:
            klass = self.pool.get(obj.data_type.model.model)
            _logger.info ("\n\nUsing Flow %s for klass %s\n", obj.name, klass)
            if obj.format_ == 'application/json':
                action = context.get('action', 'push')
                wh = self.pool.get('cenit.handler')
                context.update({'receive_object': True})
                action = getattr(wh, action, False)
                _logger.info ("\n\nAction : %s\n", action)
                if action:
                    res = action(cr, uid, data, obj.data_type.cenit_root, context)
            elif obj.format_ == 'application/EDI-X12':
                for edi_document in data:
                    klass.edi_import(cr, uid, edi_document, context)
                res = True
        return res

    def set_send_execution(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
#         ic_obj = self.pool.get('ir.cron')
        ias_obj = self.pool.get('ir.actions.server')
        bar_obj = self.pool.get('base.action.rule')
#         if obj.execution == 'only_manual':
#             if obj.base_action_rule_id:
#                 bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
#             elif obj.ir_cron_id:
#                 ic_obj.unlink(cr, uid, [obj.ir_cron_id.id])
#         elif obj.execution == 'interval':
#             if obj.ir_cron_id:
#                 pass
#             else:
#                 vals_ic = {
#                     'name': 'push_%s' % obj.model_id.model,
#                     'interval_number': 10,
#                     'interval_type': 'minutes',
#                     'numbercall': -1,
#                     'model': 'cenit.flow',
#                     'function': 'send_all',
#                     'args': '([%s],)' % str(obj.id)
#                 }
#                 ic_id = ic_obj.create(cr, uid, vals_ic)
#                 self.write(cr, uid, obj.id, {'ir_cron_id': ic_id})
#                 if obj.base_action_rule_id:
#                     bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
#         elif obj.execution in ['on_create', 'on_write','on_create_or_write']:
        if obj.execution in ['on_create', 'on_write', 'on_create_or_write']:
            if obj.base_action_rule:
                bar_obj.write(cr, uid, obj.base_action_rule.id,
                              {'kind': obj.execution})
            else:
                cd = "self.pool.get('cenit.flow').send(cr, uid, obj, %s)"\
                    % (obj.id,)
                vals_ias = {
                    'name': 'push_%s' % obj.data_type.model.model,
                    'model_id': obj.data_type.model.id,
                    'state': 'code',
                    'code': cd
                }
                ias_id = ias_obj.create(cr, uid, vals_ias)
                vals_bar = {
                    'name': 'push_%s' % obj.data_type.model.model,
                    'active': True,
                    'kind': obj.execution,
                    'model_id': obj.data_type.model.id,
                    'server_action_ids': [(6, 0, [ias_id])]
                }
                bar_id = bar_obj.create(cr, uid, vals_bar)
                self.write(cr, uid, obj.id, {'base_action_rule': bar_id})
#                 if obj.ir_cron_id:
#                     ic_obj.unlink(cr, uid, obj.ir_cron_id.id)
        return True

    def send(self, cr, uid, model, flow_id, context=None):
        flow = self.browse(cr, uid, flow_id, context=context)
        if flow:
            data = None
            if flow.format_ == 'application/json':
                ws = self.pool.get('cenit.serializer')
                data = [ws.serialize(cr, uid, model)]
            elif flow.format_ == 'application/EDI-X12':
                data = self.pool.get(model._name).edi_export(
                    cr, uid, [model]
                )
            return self._send(cr, uid, flow.data_type, data, context)
        return False

#     def send_all(self, cr, uid, ids, context=None):
#         obj = self.browse(cr, uid, ids[0])
#         ws = self.pool.get('cenit.serializer')
#         mo = self.pool.get(obj.model_id.model, False)
#         if mo:
#             models = []
#             model_ids = mo.search(cr, uid, [], context=context)
#             if obj.format == 'json':
#                 for x in mo.browse(cr, uid, model_ids, context):
#                     models.append(ws.serialize(cr, uid, x))
#             elif obj.format == 'edi' and hasattr(mo, 'edi_export'):
#                 models = mo.edi_export(cr, uid, mo.browse(cr,uid,model_ids))
#             if model_ids:
#                 return self._send(cr, uid, obj, models, context)
#         return False

    def _send(self, cr, uid, obj, data, context=None):
        method = "http_post"
#         if local:
#             method = "local_http"
        return getattr(self, method)(cr, uid, obj, data, context)

    def http_post(self, cr, uid, obj, data, context=None):
        values = {obj.cenit_root: data}
        path = "/api/v1/push"

        rc = False
        _logger.info("\n\nHTTP Posting to Cenit values: %s\n", values)
        try:
            rc = self.post(cr, uid, path, values, context=context)
            _logger.info("\n\nResponse received: %s\n", rc)
        except Warning as e:
            _logger.exception(e)

        return rc

#     def local_post(self, cr, uid, obj, data, context=None):
#         db = context.get('partner_db')
#         if db:
#             registry = openerp.modules.registry.RegistryManager.get(db)
#             with registry.cursor() as rcr:
#                 uids = registry['res.users'].search(rcr, SI,
#                                                 [('oauth_uid', '!=', False)])
#                 ruid = uids and uids[0] or SI
#                 model = obj.root.lower()
#                 return registry['cenit.flow'].receive(rcr, ruid, model, data)
