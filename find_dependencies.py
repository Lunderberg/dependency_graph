#!/usr/bin/env python3

from collections import namedtuple
import os
import subprocess
import sys

Symbol = namedtuple('Symbol',['mangled','demangled'])

class SharedObjectLib:
    def __init__(self, filename):
        self.filename = filename
        self._ParseSymbols()

    @property
    def shortname(self):
        basename = os.path.basename(self.filename)
        if basename.startswith('lib') and basename.endswith('.so'):
            return basename[3:-3]
        else:
            return basename

    def _ParseSymbols(self):
        resolved_symbols = []
        unresolved_symbols = []

        text = subprocess.check_output(['nm',self.filename])
        text = text.decode('UTF-8')
        for line in text.split('\n'):
            if len(line) < 19:
                continue

            try:
                address = int(line[:16],base=16)
            except ValueError:
                address = None
            status = line[17]
            symbol = line[18:].strip()

            if address is None:
                unresolved_symbols.append(symbol)
            else:
                resolved_symbols.append(symbol)

        self.resolved_symbols = self._UnmangleSymbols(resolved_symbols)
        self.unresolved_symbols = self._UnmangleSymbols(unresolved_symbols)

    def _UnmangleSymbols(self, symbols):
        text = subprocess.check_output(['c++filt'] + symbols)
        text = text.decode('UTF-8')
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return set(Symbol(mangled, demangled)
                   for mangled,demangled in zip(symbols, lines))

    def DependsOn(self,library):
        return not self.unresolved_symbols.isdisjoint(library.resolved_symbols)

if __name__=='__main__':
    libraries = {os.path.basename(libpath):SharedObjectLib(libpath) for libpath in sys.argv[1:]}

    for nameA, libA in libraries.items():
        for nameB, libB in libraries.items():
            if libA.DependsOn(libB):
                print('{} -> {}'.format(libA.shortname, libB.shortname))
