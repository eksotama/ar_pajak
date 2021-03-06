# -*- encoding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################


from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from datetime import datetime
from tools.translate import _

class faktur_pajak(osv.osv):
    _name = 'pajak.faktur_pajak'
    _description = 'Faktur Pajak'
    _inherit = ['mail.thread']
    
    def default_state(self, cr, uid, context={}):
        return 'draft'
        
    def default_name(self, cr, uid, context={}):
        return '/'
        
    def default_company_id(self, cr, uid, context={}):
        obj_res_company = self.pool.get('res.company')

        company_id = obj_res_company._company_default_get(cr, uid, 'res.partner', context=context)
        return company_id
        
    def default_faktur_pajak_date(self, cr, uid, context={}):
        return datetime.now().strftime('%Y-%m-%d')
        
    def default_created_time(self, cr, uid, context={}):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    def default_created_user_id(self, cr, uid, context={}):
        return uid

    def function_nomor_seri(self, cr, uid, ids, name, args, context=None):
        #TODO: Ticket #117
        res = {}
        for faktur in self.browse(cr, uid, ids):
            res[faktur.id] = faktur.jenis_transaksi_faktur_pajak_id.code + faktur.status_faktur_pajak_id.code + '.' + faktur.kode_cabang + '-' + faktur.kode_tahun + '.' + faktur.name
        return res

    def function_amount_all(self, cr, uid, ids, name, args, context=None):
        #TODO: Tiket 11
        res = {}

        for faktur in self.browse(cr, uid, ids):
            untaxed = 0.0
            base = 0.0
            amount_tax = 0.0
            total_ppnbm = 0.0

            if faktur.faktur_pajak_line_ids:
                for line in faktur.faktur_pajak_line_ids:
                    base += line.subtotal            

                untaxed = (base - faktur.discount - faktur.advance_payment) 
                amount_tax = (0.1 * untaxed)

            if faktur.faktur_pajak_line_ppnbm_ids:
                for line in faktur.faktur_pajak_line_ppnbm_ids:
                    total_ppnbm += line.ppnbm_amount

            res[faktur.id] =    {
                                'untaxed' : untaxed,
                                'base' : base,
                                'amount_tax' : amount_tax,
                                'total_ppnbm' : total_ppnbm,
                                }
        return res
    
            
    
    _columns =  {
                'name' : fields.char(string='# Faktur Pajak', size=8, required=True, readonly=True),
                'jenis_transaksi_faktur_pajak_id' : fields.many2one(string='Jenis Transaksi', obj='pajak.jenis_transaksi_faktur_pajak', required=True),
                'status_faktur_pajak_id' : fields.many2one(string='Status', obj='pajak.status_faktur_pajak', required=True),
                'kode_cabang' : fields.char(string='Kode Cabang', size=3, required=True),
                'kode_tahun' : fields.char(string='Kode Tahun', size=2, required=True),
                'nomor_seri' : fields.function(string='Nomor Seri', fnct=function_nomor_seri, type='char', size=30, method=True, store=True),
                'company_id' : fields.many2one(obj='res.company', string='Company', required=True),
                'company_npwp' : fields.char(string='Company NPWP', size=30, required=True),
                'company_address' : fields.char(string='Company Address', size=255, required=True),
                'tanggal_pengukuhan_pkp' : fields.date(string='Tanggal Pengukuhan PKP', required=True),
                'nppkp' : fields.char(string='NPPKP', size=50),
                'partner_id' : fields.many2one(obj='res.partner', string='Partner', required=True),
                'partner_npwp' : fields.char(string='Partner NPWP', size=30, required=True),
                'partner_address' : fields.char(string='Partner Address', size=100, required=True),
                'signature_id' : fields.many2one(obj='res.users', string='Signature', readonly=False, required=True),
                'signature_job' : fields.char(string='Job', size=100, required=True),
                'discount' : fields.float(string='Discount', digits_compute=dp.get_precision('Account'), required=True),
                'advance_payment' : fields.float(string='Amount Advance Payment', digits_compute=dp.get_precision('Account'), required=True),
                'untaxed' : fields.function(fnct=function_amount_all, type='float', string='Untaxed', digits_compute=dp.get_precision('Account'), method=True, store=True, multi='all'),
                'base' : fields.function(fnct=function_amount_all, type='float', string='Base', digits_compute=dp.get_precision('Account'), method=True, store=True, multi='all'),
                'total_ppnbm' : fields.function(fnct=function_amount_all, type='float', string='Total PPnBM', digits_compute=dp.get_precision('Account'), method=True, store=True, multi='all'),
                'amount_tax' : fields.function(fnct=function_amount_all, string='Amount Tax', digits_compute=dp.get_precision('Account'), method=True, store=True, multi='all'),
                'faktur_pajak_line_ids' : fields.one2many(obj='pajak.faktur_pajak_line', fields_id='faktur_pajak_id', string='Faktur Pajak Line'),
                'faktur_pajak_line_ppnbm_ids' : fields.one2many(obj='pajak.faktur_pajak_ppnbm_line', fields_id='faktur_pajak_id', string='Faktur Pajak PPN Bm Line'),
                'faktur_pajak_date' : fields.date(string='Date', required=True),
                'city' : fields.char(string='City', size=100, required=True),
                'note' : fields.text(string='Note'),
                'state' : fields.selection([('draft','Draft'),('confirm','Waiting For Approval'),('approve','Ready To Process'),('done','Done'),('cancel','Cancel')], 'Status', readonly=True),
                'created_time' : fields.datetime(string='Created Time', readonly=True),
                'created_user_id' : fields.many2one(string='Created By', obj='res.users', readonly=True),
                'confirmed_time' : fields.datetime(string='Confirmed Time', readonly=True),
                'confirmed_user_id' : fields.many2one(string='Confirmed By', obj='res.users', readonly=True),                       
                'approved_time' : fields.datetime(string='Approved Time', readonly=True),
                'approved_user_id' : fields.many2one(string='Approved By', obj='res.users', readonly=True),     
                'processed_time' : fields.datetime(string='Processed Time', readonly=True),
                'processed_user_id' : fields.many2one(string='Process By', obj='res.users', readonly=True),             
                'cancelled_time' : fields.datetime(string='Processed Time', readonly=True),
                'cancelled_user_id' : fields.many2one(string='Process By', obj='res.users', readonly=True),                                                                                             
                'cancelled_reason' : fields.text(string='Cancelled Reason', readonly=True),
                }   
                
    _defaults = {
                'name' : default_name,
                'company_id' : default_company_id,
                'faktur_pajak_date' : default_faktur_pajak_date,
                'state' : default_state,
                'created_time' : default_created_time,
                'created_user_id' : default_created_user_id,
                }

    def workflow_action_confirm(self, cr, uid, ids, context={}):
        for id in ids:
            if not self.log_audit_trail(cr, uid, id, 'confirmed'):
                return False

        return True

    def workflow_action_approve(self, cr, uid, ids, context={}):
        for id in ids:
            if not self.log_audit_trail(cr, uid, id, 'approved'):
                return False

        return True         
        
    def workflow_action_done(self, cr, uid, ids, context={}):
        for id in ids:
            if not self.log_audit_trail(cr, uid, id, 'processed'):
                return False

        return True     
        
    def workflow_action_cancel(self, cr, uid, ids, context={}):
        for id in ids:
            if not self.log_audit_trail(cr, uid, id, 'cancelled'):
                return False
            if not self.write_cancel_sequence(cr, uid, id):
                return False
        return True     
        
    def onchange_company_id(self, cr, uid, ids, company_id):
        #TODO: Ticket #7
        obj_res_company = self.pool.get('res.company')
        obj_partner = self.pool.get('res.partner')

        value = {}
        domain = {}
        warning = {}
       
        if company_id:
            company = obj_res_company.browse(cr, uid, [company_id])[0]
            value.update({'company_npwp' : company.partner_id.npwp,
                            'signature_id' : company.faktur_pajak_signature_id and company.faktur_pajak_signature_id.id or False,
                            'tanggal_pengukuhan_pkp' : company.partner_id.tanggal_pengukuhan_pkp,
                            'company_address' : obj_partner.address_get(cr, uid, [company.partner_id.id])['default']
                            })

        return {'value' : value, 'domain' : domain, 'warning' : warning}

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        #TODO: Ticket #8

        obj_res_partner = self.pool.get('res.partner')

        value = {}
        domain = {}
        warning = {}

        if partner_id:
            npwp = obj_res_partner.browse(cr, uid, partner_id).npwp
            value.update({'partner_npwp' : npwp})
        
        return {'value' : value, 'domain' : domain, 'warning' : warning}
        
    def create_sequence(self, cr, uid, id):
        #TODO: Ticket #9
        
        obj_sequence = self.pool.get('ir.sequence')
        obj_faktur_pajak_sequence = self.pool.get('pajak.faktur_pajak_sequence')

        faktur_pajak = self.browse(cr, uid, [id])[0]
        
        if faktur_pajak.company_id.sequence_faktur_pajak:
            sequence = obj_sequence.next_by_id(cr, uid, faktur_pajak.company_id.sequence_faktur_pajak.id)
            self.write(cr, uid, [id], {'name' : sequence})
            
            val = { 'name' : sequence,
                    'faktur_pajak_id' : faktur_pajak.id,
            }
            obj_faktur_pajak_sequence.create(cr, uid, val)
        else:
            raise osv.except_osv(_('Peringatan'),_('Sequence Faktur Pajak Belum Di-Set'))
            return False

        return True
        
    def select_sequence(self, cr, uid, id, faktur_pajak_sequence_id):
        """
        Parameter :
        faktur_pajak_sequence : char
        """
        #TODO: Ticket #10
        obj_faktur_pajak_sequence = self.pool.get('pajak.faktur_pajak_sequence')

        faktur_pajak = self.browse(cr, uid, [id])[0]
        
        kriteria = [('id','=', faktur_pajak_sequence_id)]
        faktur_pajak_sequence_ids = obj_faktur_pajak_sequence.search(cr, uid, kriteria)

        if faktur_pajak_sequence_ids:
            faktur_pajak_sequence = obj_faktur_pajak_sequence.browse(cr, uid, faktur_pajak_sequence_ids)[0]
            self.write(cr, uid, [faktur_pajak.id], {'name' : faktur_pajak_sequence.name})
            obj_faktur_pajak_sequence.write(cr, uid, [faktur_pajak_sequence_id], {'faktur_pajak_id' : faktur_pajak.id})
        return True

    def write_cancel_description(self, cr, uid, id, reason):
        self.write(cr, uid, [id], {'cancelled_reason' : reason})
        return True

    def write_cancel_sequence(self, cr, uid, id):
        obj_faktur_pajak_sequence = self.pool.get('pajak.faktur_pajak_sequence')

        faktur_pajak = self.browse(cr, uid, [id])[0]

        kriteria = [('faktur_pajak_id', '=', faktur_pajak.id)]
        faktur_pajak_sequence_ids = obj_faktur_pajak_sequence.search(cr, uid, kriteria)

        if faktur_pajak_sequence_ids:
            faktur_pajak_sequence = obj_faktur_pajak_sequence.browse(cr, uid, faktur_pajak_sequence_ids)[0]

            obj_faktur_pajak_sequence.write(cr, uid, [faktur_pajak_sequence.id], {'faktur_pajak_id' : False})
        else:
            return False

        self.write(cr, uid, [faktur_pajak.id], {'name' : '/'})
        return True

    def button_action_set_to_draft(self, cr, uid, ids, context={}):
        for id in ids:
            if not self.delete_workflow_instance(cr, uid, id):
                return False

            if not self.create_workflow_instance(cr, uid, id):
                return False

            if not self.clear_log_audit(cr, uid, id):
                return False

            if not self.log_audit_trail(cr, uid, id, 'created'):
                return False
                
        return True

        
    def button_action_cancel(self, cr, uid, ids, context={}):

        wkf_service = netsvc.LocalService('workflow')
        for id in ids:
            if not self.delete_workflow_instance(r, uid, id):
                return False

            if not self.create_workflow_instance(cr, uid, id):
                return False

            if not self.write_cancel_sequence(cr, uid, id):
                return False

            wkf_service.trg_validate(uid, 'pajak.faktur_pajak', id, 'button_cancel', cr)

        return True

    def clear_log_audit(self, cr, uid, id):
        #TODO: Ticket #110
        val =	{
                'created_user_id' : False,
                'created_time' : False,		
                'confirmed_user_id' : False,
                'confirmed_time' : False,
                'approved_user_id' : False,
                'approved_time' : False,
                'processed_user_id' : False,
                'processed_time' : False,
                'cancelled_user_id' : False,
                'cancelled_time' : False,
                }
			
        self.write(cr, uid, [id], val)

        return True

    def log_audit_trail(self, cr, uid, id, state):
        #TODO: Ticket #12
        if state not in ['created','confirmed','approved','processed','cancelled']:
            raise osv.except_osv(_('Peringatan!'),_('Error pada method log_audit'))
            return False
            
        state_dict =    {
                        'created' : 'draft',
                        'confirmed' : 'confirm',
                        'approved' : 'approve',
                        'processed' : 'done',
                        'cancelled' : 'cancel'
                        }
                
        val =   {
                '%s_user_id' % (state) : uid ,
                '%s_time' % (state) : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'state' : state_dict.get(state, False),
                }          
        self.write(cr, uid, [id], val)
        return True

    def delete_workflow_instance(self, cr, uid, id):
        #TODO: Ticket #13

        wkf_service = netsvc.LocalService('workflow')
        wkf_service.trg_delete(uid, 'pajak.faktur_pajak', id, cr)

        return True

    def create_workflow_instance(self, cr, uid, id):
        #TODO: Ticket #14

        wkf_service = netsvc.LocalService('workflow')
        wkf_service.trg_create(uid, 'pajak.faktur_pajak', id, cr)

        return True

faktur_pajak()

class faktur_pajak_line(osv.osv):
    _name = 'pajak.faktur_pajak_line'
    _description = 'Faktur Pajak Line'
    
    _columns =  {
                'name' : fields.char('Description', size=100, required=True),
                'product_id' : fields.many2one(obj='product.product', string='Product'),
                'faktur_pajak_id' : fields.many2one(obj='pajak.faktur_pajak', string='# Faktur Pajak'),
                'subtotal':fields.float(string='Subtotal', digits_compute=dp.get_precision('Account')),
                }   

    def onchange_product_id(self, cr, uid, ids, product_id):
        #TODO: Ticket #114
        value = {}
        domain = {}
        warning = {}

        obj_product = self.pool.get('product.product')

        kriteria = [('id', '=', product_id)]
        product_ids = obj_product.search(cr, uid, kriteria)

        if product_ids:
            product = obj_product.browse(cr, uid, product_ids)[0]
            value.update({'subtotal' : product.list_price, 'name' : product.name})
            
        return {'value' : value, 'domain' : domain, 'warning' : warning}

faktur_pajak_line()

class faktur_pajak_ppnbm_line(osv.osv):
    _name = 'pajak.faktur_pajak_ppnbm_line'
    _description = 'Faktur Pajak PPNBm Line'

    def function_ppnbm_amount(self, cr, uid, ids, name, args, context=None):
        #TODO: Ticket #111
        res = {}
        for faktur_pajak_ppnbm_line in self.browse(cr, uid, ids):
            total_ppnbm_amount = 0.0
            total_ppnbm_amount = faktur_pajak_ppnbm_line.base * faktur_pajak_ppnbm_line.ppnbm_rate
            res[faktur_pajak_ppnbm_line.id] = total_ppnbm_amount
        return res
    
    _columns =  {
                'ppnbm_rate' : fields.float(string='Rate', digits=(16,9), required=True),
                'base' : fields.float(string='Base', digits_compute=dp.get_precision('Account'), required=True),
                'ppnbm_amount' : fields.function(string='PPN Bm', fnct=function_ppnbm_amount, type='float', digits_compute=dp.get_precision('Account'), method=True, store=True),
                'faktur_pajak_id' : fields.many2one(obj='pajak.faktur_pajak', string='# Faktur Pajak', ondelete='cascade'),
                }   

faktur_pajak_ppnbm_line()

class account_faktur_pajak_sequence(osv.osv):
    _name = 'pajak.faktur_pajak_sequence'
    _description = 'Faktur Pajak Sequence'
    
    _columns =  {
                'name' : fields.char('Name', size=30, readonly=True),
                'faktur_pajak_id' : fields.many2one(obj='pajak.faktur_pajak', string='# Faktur Pajak', readonly=True, ondelete='cascade'),
                }   
            

account_faktur_pajak_sequence()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
