# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool

from . import bench
from . import wizard


def register():
    Pool.register(
        bench.Bench,
        wizard.BenchResultView,
        wizard.BenchResultDetail,
        module='bench', type_='model')

    Pool.register(
        wizard.BenchResult,
        module='bench', type_='wizard')
