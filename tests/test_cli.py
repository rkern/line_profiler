from os.path import join
from sys import executable


def test_cli():
    """
    Test command line interaction with kernprof and line_profiler.

    References:
        https://github.com/pyutils/line_profiler/issues/9

    CommandLine:
        xdoctest -m ~/code/line_profiler/tests/test_cli.py test_cli
    """

    # Create a dummy source file
    import ubelt as ub
    code = ub.codeblock(
        '''
        @profile
        def my_inefficient_function():
            a = 0
            for i in range(10):
                a += i
                for j in range(10):
                    a += j

        if __name__ == '__main__':
            my_inefficient_function()
        ''')
    import tempfile
    tmp_dpath = tempfile.mkdtemp()
    tmp_src_fpath = join(tmp_dpath, 'foo.py')
    ub.writeto(tmp_src_fpath, code)

    # Run kernprof on it
    info = ub.cmd('kernprof -l {}'.format(tmp_src_fpath), verbose=3,
                  cwd=tmp_dpath)
    assert info['ret'] == 0

    tmp_lprof_fpath = join(tmp_dpath, 'foo.py.lprof')
    tmp_lprof_fpath

    info = ub.cmd('{} -m line_profiler {}'.format(executable,tmp_lprof_fpath),
                  cwd=tmp_dpath, verbose=3)
    assert info['ret'] == 0
    # Check for some patterns that should be in the output
    assert '% Time' in info['out']
    assert '7       100' in info['out']


def test_version_agreement():
    """
    Ensure that line_profiler and kernprof have the same version info
    """
    import ubelt as ub
    info1 = ub.cmd('{} -m line_profiler --version'.format(executable))
    info2 = ub.cmd('{} -m kernprof --version'.format(executable))

    # Strip local version suffixes
    version1 = info1['out'].strip().split('+')[0]
    version2 = info2['out'].strip().split('+')[0]

    assert version2 == version1, 'kernprof and line_profiler must be in sync'
