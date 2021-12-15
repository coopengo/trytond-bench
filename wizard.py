# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal

from trytond.i18n import gettext
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, Button


class BenchResult(Wizard):
    'Benchmark Result'
    __name__ = 'bench.result'

    start = StateView('bench.result.view', 'bench.bench_result_view_form',
        buttons=[Button('Ok', 'end', 'tryton-ok')])

    def default_start(self, name):
        results = Transaction().context.get('bench_results', None)
        if not results:
            raise UserError(gettext('bench.msg_use_plugin'))
        return {
            'results': [self.generate_displayer(x)
                for x in results if 'results' in x],
            }

    def generate_displayer(self, raw_data):
        converted_data = {
            key: Decimal(str(raw_data['results'][key])).quantize(
                Decimal('0.00001'))
            for key in ('average', 'minimum', 'maximum', 'slowest')}
        converted_data['name'] = raw_data['name']
        return converted_data


class BenchResultView(ModelView):
    'Benchmark Result View'
    __name__ = 'bench.result.view'

    results = fields.One2Many('bench.result.detail', None, 'Results',
        readonly=True)


class BenchResultDetail(ModelView):
    'Benchmark Result Detail'
    __name__ = 'bench.result.detail'

    name = fields.Char('Name', readonly=True)
    average = fields.Numeric('Average', readonly=True)
    minimum = fields.Numeric('Minimum', readonly=True)
    maximum = fields.Numeric('Maximum', readonly=True)
    slowest = fields.Numeric('Slowest (including warmup)', readonly=True)
