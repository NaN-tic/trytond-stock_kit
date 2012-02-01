# -*- encoding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name' : 'Stock Product Kit',
    'version' : '2.3.0',
    'author' : 'NaN·tic',
    'email': 'info@nan-tic.com',
    'website': 'http://www.nan-tic.com/',
    'description': 'Allows product kits to be exploded in shipments and make '
            'their stock (real and forecast) depend on the stock of its '
            'components',
    'depends' : [
	'stock',
        'product_kit',
    ],
    'xml' : [
        'product.xml',
    ],
    'translation': [
    ]
}
