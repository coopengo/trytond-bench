import gc
from timeit import default_timer as timer
import datetime

from sql import Table, Literal

from trytond import backend
from trytond.model import Model
from trytond.rpc import RPC
from trytond.transaction import Transaction


__all__ = [
    'Bench',
    ]


def do_bench(iterations=10, collect=False):
    def decorator(f):
        def wrapped(*args, **kwargs):
            times = []
            for _ in range(iterations):
                if collect:
                    gc.collect()
                start = timer()
                f(*args, **kwargs)
                end = timer()
                times.append(end - start)

            # Remove min / max values
            times = sorted(times)[1:-1]
            average = sum(times[1:-1]) / (len(times) - 2)
            return {
                'iterations': iterations,
                'average': average,
                'minimum': times[1],
                'maximum': times[-2],
                'slowest': times[-1],
                }
        return wrapped
    return decorator


class Bench(Model):
    'Benchmark class for tools'

    __name__ = 'bench'

    @classmethod
    def __setup__(cls):
        super(Bench, cls).__setup__()
        cls.__rpc__['list'] = RPC(readonly=False)
        cls.__rpc__['setup'] = RPC(readonly=False)
        cls.__rpc__['teardown'] = RPC(readonly=False)
        cls.__rpc__['test_latency'] = RPC(readonly=True)
        cls.__rpc__['test_cpu'] = RPC(readonly=True)
        cls.__rpc__['test_memory'] = RPC(readonly=True)
        cls.__rpc__['test_db_latency'] = RPC(readonly=False)
        cls.__rpc__['test_db_write'] = RPC(readonly=False)
        cls.__rpc__['test_db_read'] = RPC(readonly=False)

    @classmethod
    def list(cls):
        '''
        List of available benchmarks

        A benchmark will have:
            - name: The name of the benchmark, only used for the reports
            - setup: A boolean, must be true if the setup step is required
              before execution
            - type: One of
              * latency: Special type, with no parameters, the client will call
                "test_latency" to evaluate client / server latency
              * server: Benchmarks a rpc method on the server, without
                parameters
              * act_window: Benchmarks client side the opening of an act window
                There are two parameters:
                  + action_id: The xml id of the act window (mandatory)
                  + switch_view: If the client should switch to form view (
                    defaults to False)
        '''
        return {
            'setup': 'setup',
            'teardown': 'teardown',
            'methods': [
                {
                    'name': 'Latency (client/server)',
                    'type': 'latency',
                    'parameters': {},
                    'setup': False,
                },
                {
                    'name': 'CPU (10M OPs)',
                    'type': 'server',
                    'parameters': {'method': 'test_cpu'},
                    'setup': False,
                },
                {
                    'name': 'Memory (1GB alloc)',
                    'type': 'server',
                    'parameters': {'method': 'test_memory'},
                    'setup': False,
                },
                {
                    'name': 'DB Latency (1K pings)',
                    'type': 'server',
                    'parameters': {'method': 'test_db_latency'},
                    'setup': False,
                },
                {
                    'name': 'DB Read (100K records)',
                    'type': 'server',
                    'parameters': {'method': 'test_db_read'},
                    'setup': True,
                },
                {
                    'name': 'DB Write (2K records)',
                    'type': 'server',
                    'parameters': {'method': 'test_db_write'},
                    'setup': True,
                },
                ]}

    @classmethod
    def setup(cls):
        cursor = Transaction().connection.cursor()

        if backend.name != 'postgresql':
            raise Exception('Database must be postgresql !')

        # Check for test table
        table = Table('tables', 'information_schema')
        for schema in Transaction().database.search_path:
            cursor.execute(*table.select(Literal(1),
                    where=(table.table_name == 'benchmark_table')
                    & (table.table_schema == schema)))
            if cursor.rowcount:
                raise Exception('Benchmark table already in, run '
                    'teardown and try again')

        # Create table
        cursor.execute('CREATE TABLE "benchmark_table" ('
            'id integer PRIMARY KEY,'
            'some_string varchar(100),'
            'some_date date)')

    @classmethod
    def teardown(cls):
        cursor = Transaction().connection.cursor()
        cursor.execute('DROP TABLE "benchmark_table"')

    @classmethod
    def test_latency(cls):
        return

    @classmethod
    @do_bench(100)
    def test_cpu(cls):
        for x in range(10000000):
            pass

    @classmethod
    @do_bench(100, collect=True)
    def test_memory(cls):
        ['x'] * 1024  # Multiple small allocations
        'x' * 512000000  # The big one

    @classmethod
    @do_bench(100)
    def test_db_latency(cls):
        cursor = Transaction().connection.cursor()
        for x in range(1000):
            cursor.execute('SELECT 1')

    @classmethod
    def write_db_data(cls, nb):
        bench_table = Table('benchmark_table')
        cursor = Transaction().connection.cursor()
        cursor.execute(*bench_table.delete(where=bench_table.id >= 0))
        for x in range(nb):
            cursor.execute(*bench_table.insert(
                    columns=[bench_table.id, bench_table.some_string,
                        bench_table.some_date],
                    values=[[x, str(x) * 10, datetime.date(2016, 1, 1)]]))

    @classmethod
    @do_bench(100)
    def test_db_write(cls):
        cls.write_db_data(2000)

    @classmethod
    @do_bench(100)
    def _test_db_read(cls):
        cursor = Transaction().connection.cursor()
        cursor.execute('SELECT * FROM "benchmark_table" AS a')
        assert(len(cursor.fetchall()) == 100000)

    @classmethod
    def test_db_read(cls):
        cls.write_db_data(100000)
        return cls._test_db_read()
