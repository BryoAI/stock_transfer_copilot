import datetime
import json
import requests
from odoo import api, fields, models, _
import pandas as pd
from .create_llm_prompt import askai
# from utils import create_llm_prompt
from odoo.exceptions import UserError


class Channel(models.Model):
    _inherit = 'mail.channel'

    # The if conditions are there to stop the recursion! Research about why they are there and how can we remove them
    def _notify_thread(self, message, msg_vals=False, **kwargs):
        rdata = super(Channel, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)
        bard_suggestions_channel = self.env.ref('stock_transfer_copilot.channel_bard_suggestions')
        copilot_user = self.env.ref("stock_transfer_copilot.copilot_user")
        partner_copilot = self.env.ref("stock_transfer_copilot.copilot_user_partner")
        author_id = msg_vals.get('author_id')
        copilot_name = str(partner_copilot.name or '') + ', '
        prompt = msg_vals.get('body')
        if not prompt:
            return rdata
        Partner = self.env['res.partner']
        if author_id:
            partner_id = Partner.browse(author_id)
            if partner_id:
                partner_name = partner_id.name

        if author_id != partner_copilot.id and copilot_name in msg_vals.get('record_name', '') or 'ChatGPT,' in msg_vals.get('record_name', '') and self.channel_type == 'chat':
            try:
                res = "Here is the history of all the messages in this channel:"
                messages = self.message_ids
                history = ''
                for message in messages:
                    temp_author_id = message.author_id.id
                    # print(str(temp_author_id.id))
                    # print(type(temp_author_id.id))
                    author_name = self.env['res.partner'].search([('id', '=', temp_author_id)]).name
                    if message.body:
                        history += f'{author_name}: {message.body}'
                        history += '\n'
                    else:
                        history += f'{author_name}: {"no message"}'
                        history += '\n'
                    history += '\n'
                history += '---------------------------'
                history += '\n'
                res += '\n\n**Message History**\n' + history
                res = askai(res)
                self.with_user(copilot_user).message_post(body=res, message_type='comment', subtype_xmlid='mail.mt_comment')
            except Exception as e:
                raise UserError(_(e))

        elif author_id != partner_copilot.id and msg_vals.get('model', '') == 'mail.channel' and msg_vals.get('res_id', 0) == bard_suggestions_channel.id:
            try:
                res = "*****THIS IS A TEST BARD SUGGESTION*****"
                res = "Here is the history of all the messages in this channel:"
                messages = self.message_ids
                history = ''
                for message in messages:
                    # extract name of message sender from message
                    temp_author_id = message.author_id.id
                    # print(str(temp_author_id.id))
                    # print(type(temp_author_id.id))
                    author_name = self.env['res.partner'].search([('id', '=', temp_author_id)]).name
                    if message.body:
                        history += f'{author_name}: {message.body}'
                        history += '\n'
                    else:
                        history += f'{author_name}: {"no message"}'
                        history += '\n'
                    history += '---------------------------'
                    history += '\n'
                res += '\n\n**Message History**\n' + history
                res = askai(res)
                bard_suggestions_channel.with_user(copilot_user).message_post(body=res, message_type='comment', subtype_xmlid='mail.mt_comment')
            except Exception as e:
                raise UserError(_(e))
        return rdata