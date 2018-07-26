"""Global tests configuration"""
import collections
import distutils.dir_util  # pylint: disable=no-name-in-module,import-error
import os
from subprocess import Popen, PIPE
import pytest


@pytest.fixture(scope='session')
def shellcheck_version():
    """Version of shellcheck supported"""
    return '0.4.6'


@pytest.fixture(scope='session')
def pylint_version():
    """Version of pylint supported"""
    return '1.9.2'


@pytest.fixture(scope='session')
def flake8_version():
    """Version of flake8 supported"""
    return '3.5.0'


class Runner(object):
    """Class for running commands"""

    def __init__(
            self,
            command,
            inp=None,
            shell=False,
            cwd=None,
            env=None,
            label=None):
        self.label = label
        self.command = command
        self.inp = inp
        process = Popen(
            self.command,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=shell,
            cwd=cwd,
            env=env,
        )
        (self.out, self.err) = process.communicate(input=inp)
        self.code = process.wait()
        self.success = self.code == 0
        self.failure = self.code != 0

    def __repr__(self):
        if self.label:
            return 'CMD(%s)' % self.label
        return 'CMD%s' % str(self.command)

    def report(self):
        """Print code/stdout/stderr"""
        print '%s' % self
        print '  code:%s' % self.code
        print '  stdout:%s' % self.out
        print '  stderr:%s' % self.err


@pytest.fixture(scope='session')
def runner():
    """Class for running commands"""
    return Runner


@pytest.fixture(scope='session')
def config_git(runner):
    """Configure global git configuration, if missing"""
    print 'CONFIG-GIT-GLOBAL'
    runner(command=[
        'bash',
        '-c',
        'git config user.name || '
        'git config --global user.name "test"',
        ])
    runner(command=[
        'bash',
        '-c',
        'git config user.email || '
        'git config --global user.email "test@test.test"',
        ])
    return None


@pytest.fixture(scope='session')
def yadm():
    """Path to yadm program to be tested"""
    full_path = os.path.realpath('yadm')
    assert os.path.isfile(full_path), "yadm program file isn't present"
    return full_path


@pytest.fixture()
def paths(tmpdir, yadm):
    """Function scoped test paths"""
    dir_root = tmpdir.mkdir('root')
    dir_work = dir_root.mkdir('work')
    dir_yadm = dir_root.mkdir('yadm')
    dir_repo = dir_yadm.mkdir('repo.git')
    file_config = dir_yadm.join('config')
    file_bootstrap = dir_yadm.join('bootstrap')
    paths = collections.namedtuple(
        'Paths', [
            'pgm',
            'root',
            'work',
            'yadm',
            'repo',
            'config',
            'bootstrap',
            ])
    return paths(
        yadm,
        dir_root,
        dir_work,
        dir_yadm,
        dir_repo,
        file_config,
        file_bootstrap,
        )


@pytest.fixture()
def yadm_y(paths):
    """Generate custom command_list function"""
    def command_list(*args):
        """Produce params for running yadm with -Y"""
        return [paths.pgm, '-Y', str(paths.yadm)] + list(args)
    return command_list


class DataFile(object):
    """Datafile object"""

    def __init__(self, path, tracked=True, private=False):
        self._path = path
        self._tracked = tracked
        self._private = private

    @property
    def path(self):
        """Path property"""
        return self._path

    @property
    def tracked(self):
        """Tracked property"""
        return self._tracked

    @property
    def private(self):
        """Private property"""
        return self._private


class DataSet(object):
    """Dataset object"""

    def __init__(self):
        self.__files = list()
        self.__dirs = list()

    def __repr__(self):
        return '[DS with %i files; %i tracked, %i private]' % (
            len(self),
            len(self.tracked),
            len(self.private),
            )

    def __iter__(self):
        return iter(self.__files)

    def __len__(self):
        return len(self.__files)

    def __contains__(self, datafile):
        if [f for f in self.__files if f.path == datafile]:
            return True
        if datafile in self.__files:
            return True
        return False

    def add_file(self, path, tracked=True, private=False):
        """Add file to data set"""
        if path not in self:
            self.__files.append(DataFile(path, tracked, private))
        dname = os.path.dirname(path)
        if dname and dname not in self.__dirs:
            self.__dirs.append(dname)

    @property
    def files(self):
        """List of DataFiles in DataSet"""
        return list(self.__files)

    @property
    def tracked(self):
        """List of tracked DataFiles in DataSet"""
        return [f for f in self.__files if f.tracked]

    @property
    def private(self):
        """List of private DataFiles in DataSet"""
        return [f for f in self.__files if f.private]

    @property
    def dirs(self):
        """List of directories in DataSet"""
        return list(self.__dirs)

    @property
    def plain_dirs(self):
        """List of directories in DataSet not starting with '.'"""
        return [d for d in self.dirs if not d.startswith('.')]

    @property
    def hidden_dirs(self):
        """List of directories in DataSet starting with '.'"""
        return [d for d in self.dirs if d.startswith('.')]


@pytest.fixture(scope='session')
def ds1():
    """Meta-data for dataset one files"""
    dset = DataSet()
    dset.add_file('t1')
    dset.add_file('d1/t2')
    dset.add_file('u1', tracked=False)
    dset.add_file('d2/u2', tracked=False)
    dset.add_file('.ssh/p1', tracked=False, private=True)
    dset.add_file('.ssh/p2', tracked=False, private=True)
    dset.add_file('.gnupg/p3', tracked=False, private=True)
    dset.add_file('.gnupg/.p4', tracked=False, private=True)
    return dset


@pytest.fixture(scope='session')
def ds1_data(tmpdir_factory, ds1, runner):
    """A set of test data, worktree & repo"""
    config_git(runner)
    data = tmpdir_factory.mktemp('ds1')

    work = data.mkdir('work')
    for datafile in ds1:
        work.join(datafile.path).write(datafile.path, ensure=True)

    repo = data.mkdir('repo.git')
    env = os.environ.copy()
    env['GIT_DIR'] = str(repo)
    runner(
        command=['git', 'init', '--shared=0600', '--bare', str(repo)])
    runner(
        command=['git', 'config', 'core.bare', 'false'],
        env=env)
    runner(
        command=['git', 'config', 'status.showUntrackedFiles', 'no'],
        env=env)
    runner(
        command=['git', 'config', 'yadm.managed', 'true'],
        env=env)
    runner(
        command=['git', 'config', 'core.worktree', str(work)],
        env=env)
    runner(
        command=['git', 'add'] +
        [str(work.join(f.path)) for f in ds1 if f.tracked],
        env=env).report()
    runner(
        command=['git', 'commit', '--allow-empty', '-m', 'Initial commit'],
        env=env)

    data = collections.namedtuple('Data', ['work', 'repo'])
    return data(work, repo)


@pytest.fixture()
def ds1_work_copy(ds1_data, paths):
    """Function scoped copy of ds1_data.work"""
    print "COPY DS1.work"
    distutils.dir_util.copy_tree(  # pylint: disable=no-member
        str(ds1_data.work), str(paths.work))
    return None


@pytest.fixture()
def ds1_repo_copy(runner, ds1_data, paths):
    """Function scoped copy of ds1_data.repo"""
    print "COPY DS1.repo"
    distutils.dir_util.copy_tree(  # pylint: disable=no-member
        str(ds1_data.repo), str(paths.repo))
    env = os.environ.copy()
    env['GIT_DIR'] = str(paths.repo)
    runner(
        command=['git', 'config', 'core.worktree', str(paths.work)],
        env=env)
    return None


@pytest.fixture()
def ds1_copy(ds1_work_copy, ds1_repo_copy):
    """Function scoped copy of ds1_data"""
    # pylint: disable=unused-argument
    # This is ignored because
    # @pytest.mark.usefixtures('ds1_work_copy', 'ds1_repo_copy')
    # cannot be applied to another fixture.
    return None


@pytest.fixture(scope='session')
def distro(runner):
    """Distro of test system"""
    run = runner(command=['lsb_release', '-si'])
    return run.out.rstrip()
