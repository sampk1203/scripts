#!/usr/bin/env python3
"""
run_lammps.py

Thin CLI wrapper around the LAMMPS Python library that mimics the native
`lmp` binary. Every command-line flag is passed straight through to LAMMPS,
so anything `lmp` accepts works here too (-in, -log, -screen, -var with
multiple values, -pk, -sf, -k, -echo, -partition, -plog, -pscreen, -nocite,
-nonbuf, -reorder, -skiplist, ...). Built on top of the lammps-mlip-wheel
package (https://github.com/sampk1203/lammps-mlip-wheel).

Only -in / -i is read by this script, because the library interface does not
run the input file by itself (the lmp binary's main() does that). With no -in,
the script is read from stdin, like lmp.

Usage (same flags as the real `lmp` binary):
    python run_lammps.py -in in.melt
    mpirun -np 4 python run_lammps.py -in in.melt -var temp 300 -var press 1.0
    python run_lammps.py -in in.melt -log run.log -screen none
    python run_lammps.py -in in.melt -pk gpu 1 -sf gpu
    python run_lammps.py -in in.melt -var x 1 2 3
    python run_lammps.py < in.melt

Also importable for post-processing, without tearing down the LAMMPS
instance immediately after the run:

    from run_lammps import run_lammps

    l = run_lammps("in.melt", close=False)
    # l is still open here -- pull data out before closing
    natoms = l.get_natoms()
    pe = l.get_thermo("pe")
    l.close()

    # any lmp flag via cmdargs:
    l = run_lammps("in.melt", cmdargs=["-pk", "gpu", "1", "-sf", "gpu"])
"""

import sys
import traceback

from mpi4py import MPI
from lammps import lammps

# lmp flag spellings that name the input file
_IN_FLAGS = ("-in", "-i")


def split_infile(argv):
    """Return (infile, remaining_argv).

    Mimics lmp: the last -in/-i wins. infile is None if not given (stdin).
    The -in flag is left in remaining_argv; LAMMPS accepts it and ignores it
    in library mode.
    """
    infile = None
    for i, tok in enumerate(argv[:-1]):
        if tok in _IN_FLAGS:
            infile = argv[i + 1]
    return infile, list(argv)


def run_lammps(infile=None, log=None, screen=None, variables=None,
               close=True, cmdargs=None):
    """
    Run a LAMMPS input script through the Python library interface.

    Parameters
    ----------
    infile : str, optional
        Path to a LAMMPS input script (what you'd pass to `lmp -in`).
        None reads the script from stdin, like lmp.
    log : str, optional
        Path for LAMMPS's own log file. Pass "none" to suppress logging.
        Defaults to LAMMPS's own default (log.lammps) if not given.
    screen : str, optional
        Where to send LAMMPS's screen output. Pass "none" to suppress.
    variables : list[list[str, ...]], optional
        (name, value, [value ...]) entries, equivalent to
        `-var name value ...` on the lmp command line.
    close : bool, default True
        If True, close the LAMMPS instance before returning -- normal
        run-and-done use. If False, the caller owns the instance and must
        call l.close() themselves -- use this when you want to pull data
        out for post-processing (l.get_thermo(), l.numpy.extract_atom(...),
        etc.) before the instance is torn down.
    cmdargs : list[str], optional
        Any other lmp command-line flags, passed verbatim, e.g.
        ["-pk", "gpu", "1", "-sf", "gpu", "-echo", "screen"].

    Returns
    -------
    lammps.lammps
        The LAMMPS instance. Still open if close=False.

    Note: do NOT put an argv[0]/executable-name placeholder in any of these
    -- the lammps Python constructor already adds that itself.
    """
    args = []
    if log is not None:
        args += ["-log", log]
    if screen is not None:
        args += ["-screen", screen]
    if variables:
        for var in variables:
            args += ["-var", *var]
    if cmdargs:
        args += list(cmdargs)

    l = lammps(cmdargs=args)

    # Library mode does not execute the input; do it here. Rank 0 reads the
    # file/stdin, LAMMPS broadcasts to the other ranks.
    l.file(infile if infile is not None else "/dev/stdin")

    if close:
        l.close()

    return l


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    infile, lmp_args = split_infile(argv)
    rank = MPI.COMM_WORLD.Get_rank()

    try:
        run_lammps(infile, cmdargs=lmp_args, close=True)
    except Exception:
        # Still finalize MPI cleanly even if LAMMPS itself raised, so the
        # job doesn't hang waiting on ranks that never get here.
        if rank == 0:
            traceback.print_exc()
        MPI.Finalize()
        sys.exit(1)

    MPI.Finalize()


if __name__ == "__main__":
    main()
