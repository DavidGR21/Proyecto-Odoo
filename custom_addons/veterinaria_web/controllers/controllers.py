# -*- coding: utf-8 -*-
# from odoo import http


# class VeterinariaWeb(http.Controller):
#     @http.route('/veterinaria_web/veterinaria_web', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/veterinaria_web/veterinaria_web/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('veterinaria_web.listing', {
#             'root': '/veterinaria_web/veterinaria_web',
#             'objects': http.request.env['veterinaria_web.veterinaria_web'].search([]),
#         })

#     @http.route('/veterinaria_web/veterinaria_web/objects/<model("veterinaria_web.veterinaria_web"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('veterinaria_web.object', {
#             'object': obj
#         })

