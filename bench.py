from timeit import default_timer as timer

from trytond import backend
from trytond.model import Model
from trytond.rpc import RPC
from trytond.transaction import Transaction


__all__ = [
    'Bench',
    ]


def do_bench(iterations=10):
    def decorator(f):
        def wrapped(*args, **kwargs):
            times = []
            for _ in range(iterations):
                start = timer()
                f(*args, **kwargs)
                end = timer()
                times.append(end - start)
            # Remove min / max values
            times = sorted(times)
            average = sum(times[1:-1]) / (len(times) - 2)
            return "%s iterations, avg : %.5f, " % (iterations,
                average) + 'excluding min (%.5f), max (%.5f)' % (
                times[0], times[-1])
        return wrapped
    return decorator


class Bench(Model):
    'Benchmark class for tools'

    __name__ = 'utils.benchmark_class'

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
        return {
            'setup': ['setup'],
            'teardown': ['teardown'],
            'methods': [
                ('test_latency', {
                        'name': 'Latency',
                        'server_side': False,
                        'requires_setup': False,
                        }),
                ('test_cpu', {
                        'name': 'CPU',
                        'server_side': True,
                        'requires_setup': False,
                        }),
                ('test_memory', {
                        'name': 'Memory',
                        'server_side': True,
                        'requires_setup': False,
                        }),
                ('test_db_latency', {
                        'name': 'DB Latency',
                        'server_side': True,
                        'requires_setup': False,
                        }),
                ('test_db_write', {
                        'name': 'DB Write',
                        'server_side': True,
                        'requires_setup': True,
                        }),
                ('test_db_read', {
                        'name': 'DB Read',
                        'server_side': True,
                        'requires_setup': True,
                        }),
                ],
            }

    @classmethod
    def setup(cls):
        cursor = Transaction().connection.cursor()

        if backend.name() != 'postgresql':
            raise Exception('Database must be postgresql !')

        # Check for test table
        for schema in Transaction().database.search_path:
            cursor.execute('SELECT 1 FROM information_schema.tables '
                "WHERE table_name = 'benchmark_table' AND table_schema = '%s'"
                % schema)
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

        # Delete table
        cursor.execute('DROP TABLE "benchmark_table"')

    @classmethod
    def test_latency(cls):
        # Do nothing, just test complete overhead
        return

    @classmethod
    @do_bench(100)
    def test_cpu(cls):
        for x in range(10000000):
            pass

    @classmethod
    @do_bench(100)
    def test_memory(cls):
        # Allocate a lot (1GB) of space
        'x' * 1024000000

    @classmethod
    @do_bench(1000)
    def test_db_latency(cls):
        cursor = Transaction().connection.cursor()
        cursor.execute('SELECT 1')

    @classmethod
    @do_bench(10)
    def test_db_write(cls):
        cls._do_benchmark_db_write()

    @classmethod
    def _do_benchmark_db_write(cls):
        cursor = Transaction().connection.cursor()
        cursor.execute('TRUNCATE TABLE "benchmark_table"')
        for x in range(100000):
            cursor.execute('INSERT INTO "benchmark_table" (id, some_string, '
                "some_date) VALUES (%i, %s, '2016-01-01')" % (x, str(x) * 10))

    @classmethod
    def test_db_read(cls):
        # Get some data
        cls._do_benchmark_db_write()

        return cls._do_benchmark_db_read()

    @classmethod
    @do_bench(100)
    def _do_benchmark_db_read(cls):
        cursor = Transaction().connection.cursor()
        cursor.execute('SELECT * FROM "benchmark_table" AS a')

