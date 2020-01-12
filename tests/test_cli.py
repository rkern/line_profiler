from os.path import join


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

    info = ub.cmd('python -m line_profiler {}'.format(tmp_lprof_fpath),
                  cwd=tmp_dpath, verbose=3)
    assert info['ret'] == 0
    # Check for some patterns that should be in the output
    assert '% Time' in info['out']
    assert '7       100' in info['out']
