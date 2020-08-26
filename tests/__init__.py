# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    from trytond.modules.bench.tests.test_bench import suite
except ImportError:
    from .bench import suite

__all__ = ['suite']
