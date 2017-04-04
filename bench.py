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
            return {
                'iterations': iterations,
                'average': average,
                'minimum': times[0],
                'maximum': times[-1],
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
        return {
            'setup': 'setup',
            'teardown': 'teardown',
            'methods': [
                {
                    'method': 'test_latency',
                    'name': 'Latency (client/server)',
                    'server_side': False,
                    'setup': False,
                },
                {
                    'method': 'test_cpu',
                    'name': 'CPU (10M OPs)',
                    'server_side': True,
                    'setup': False,
                },
                {
                    'method': 'test_memory',
                    'name': 'Memory (1GB alloc)',
                    'server_side': True,
                    'setup': False,
                },
                {
                    'method': 'test_db_latency',
                    'name': 'DB Latency (1K pings)',
                    'server_side': True,
                    'setup': False,
                },
                {
                    'method': 'test_db_read',
                    'name': 'DB Read (100K records)',
                    'server_side': True,
                    'setup': True,
                },
                {
                    'method': 'test_db_write',
                    'name': 'DB Write (2K records)',
                    'server_side': True,
                    'setup': True,
                },
                ]}

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
    @do_bench(100)
    def test_memory(cls):
        'x' * 1024000000

    @classmethod
    @do_bench(100)
    def test_db_latency(cls):
        cursor = Transaction().connection.cursor()
        for x in range(1000):
            cursor.execute('SELECT 1')

    @classmethod
    def write_db_data(cls, nb):
        cursor = Transaction().connection.cursor()
        cursor.execute('TRUNCATE TABLE "benchmark_table"')
        for x in range(nb):
            cursor.execute('INSERT INTO "benchmark_table" (id, some_string, '
                "some_date) VALUES (%i, %s, '2016-01-01')" % (x, str(x) * 10))

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
