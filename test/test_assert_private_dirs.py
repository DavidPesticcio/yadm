"""Test asserting private directories"""
import re
import pytest

pytestmark = pytest.mark.usefixtures('ds1_copy')
PRIVATE_DIRS = ['.gnupg', '.ssh']


def test_pdirs_missing(runner, yadm_y, paths):
    """Private dirs (private dirs missing)

    When a git command is run
    And private directories are missing
    Create private directories prior to command
    """

    # confirm directories are missing at start
    for pdir in PRIVATE_DIRS:
        path = paths.work.join(pdir)
        if path.exists():
            path.remove()
        assert not path.exists()

    # run status
    run = runner(command=yadm_y('status'), env={'DEBUG': 'yes'})
    run.report()
    assert run.code == 0
    assert 'On branch master' in run.out

    # confirm directories are created
    # and are protected
    for pdir in PRIVATE_DIRS:
        path = paths.work.join(pdir)
        assert path.exists()
        assert path.stat().mode == 040700

    # confirm directories are created before command is run:
    assert re.search(
        r'Creating.+\.gnupg.+Creating.+\.ssh.+Running git command git status',
        run.out, re.DOTALL), 'directories created before command is run'


def test_pdirs_missing_apd_false(runner, yadm_y, paths):
    """Private dirs (private dirs missing / yadm.auto-private-dirs=false)

    When a git command is run
    And private directories are missing
    But auto-private-dirs is false
    Do not create private dirs
    """

    # confirm directories are missing at start
    for pdir in PRIVATE_DIRS:
        path = paths.work.join(pdir)
        if path.exists():
            path.remove()
        assert not path.exists()

    # set configuration
    run = runner(command=yadm_y(
        'config', '--bool', 'yadm.auto-private-dirs', 'false'))
    run.report()
    assert run.code == 0

    # run status
    run = runner(command=yadm_y('status'))
    run.report()
    assert run.code == 0
    assert 'On branch master' in run.out

    # confirm directories are STILL missing
    for pdir in PRIVATE_DIRS:
        assert not paths.work.join(pdir).exists()


def test_pdirs_exist_apd_false(runner, yadm_y, paths):
    """Private dirs (private dirs exist / yadm.auto-perms=false)

    When a git command is run
    And private directories exist
    And yadm is configured not to auto update perms
    Do not alter directories
    """

    # create permissive directories
    for pdir in PRIVATE_DIRS:
        path = paths.work.join(pdir)
        if not path.isdir():
            path.mkdir()
        path.chmod(0777)
        assert path.stat().mode == 040777

    # set configuration
    run = runner(command=yadm_y(
        'config', '--bool', 'yadm.auto-perms', 'false'))
    run.report()
    assert run.code == 0

    # run status
    run = runner(command=yadm_y('status'))
    run.report()
    assert run.code == 0
    assert 'On branch master' in run.out

    # create directories are STILL permissive
    for pdir in PRIVATE_DIRS:
        path = paths.work.join(pdir)
        assert path.stat().mode == 040777
