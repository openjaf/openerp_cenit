# -*- coding: utf-8 -*-

from openerp.osv.orm import TransientModel


PRODUCT = {
    'name': 'name',
    'sku': 'default_code',
    'description': 'description',
    'price': 'list_price',
    'cost_price': 'standard_price',
    #'available_on': '2014-01-01T14:01:28.000Z',
    #'shipping_category': 'Default',
}


class product_handler(TransientModel):
    _name = 'product.handler'
    _related_model = 'product.product'

    def find(self, cr, uid, params, context=None):
        if params.get('sku', False):
            p_ids = self.pool.get('product.product').search(cr, uid,
                                   [('default_code', '=', params['sku'])],
                                   context=context)
            return p_ids
        return []

    def add(self, cr, uid, params, context=None):
        res = False
        pp = self.pool.get('product.product')
        p_ids = self.find(cr, uid, params, context)
        if not p_ids:
            vals = {v: params[k] for k, v in PRODUCT.items()}
            vals['categ_id'] = self.process_taxons(cr, uid, params.get('taxons', []), context)
            vals['product_variant_ids'] = self.process_variants(cr, uid, params.get('variants', []), context)
            res = pp.create(cr, uid, vals, context)
        return res

    def update(self, cr, uid, params, context=None):
        res = False
        pp = self.pool.get('product.product')
        p_ids = self.find(cr, uid, params, context)
        if p_ids:
            vals = {k: params[v] for k, v in PRODUCT.items()}
            vals['categ_id'] = self.process_taxons(cr, uid, params.get('taxons', []), context)
            vals['product_variant_ids'] = [(2, x.id) for x in pp.browse(cr, uid, p_ids[0]).product_variant_ids]
            vals['product_variant_ids'] += self.process_variants(cr, uid, params.get('variants', []), context)
            res = pp.write(cr, uid, p_ids, vals, context)
        return res

    # TODO: it process just the first one list
    # where do we have to insert the others this?
    def process_taxons(self, cr, uid, taxons, context=None):
        if not taxons:
            return False
        pc = self.pool.get('product.category')
        current_tx = False
        for tx in taxons[0]:
            categ_id = pc.search(cr, uid, [('name', '=', tx)], context=context)
            if categ_id:
                current_tx = categ_id[0]
            else:
                vals = {'name': tx, 'parent_id': current_tx}
                current_tx = pc.create(cr, uid, vals, context)
        return current_tx

    # TODO: find how to set prices in variants
    def process_variants(self, cr, uid, variants, context):
        res = []
        for var in variants:
            vals = {
                'default_code': var['sku'],
                'variants': ' - '.join([k + ':' + v for k, v in var['options'].items()])
            }
            res.append((0, 0, vals))
        return res
