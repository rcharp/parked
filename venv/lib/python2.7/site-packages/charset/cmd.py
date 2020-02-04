# -*- coding: utf-8 -*-

"""
This file is part of the textextractor python package
Copyrighted by Karel Vedecia Ortiz <kverdecia@uci.cu, kverdecia@gmail.com>
License: MPL 2.0 (http://www.mozilla.org/MPL/2.0/)
"""
import sys
import os
import optparse
import pkg_resources
import inspect
import magic
from charset import CheckDetector
from charset import Detector


version = pkg_resources.get_distribution('charset').version
usage = "%prog [options] path"


_ = lambda x: x

class CmdCharset(object):
    parser = optparse.OptionParser(version="%prog " + version, usage=usage)
    parser.add_option('-e', '--encoding', action="store",
        dest='encoding', default=None, 
        help=_(u"Convierte los ficheros a la codificación especificada."))
    parser.add_option('-n', '--no_mimetype', action="store_true",
        dest='no_mimetype', default=False, 
        help=_(u"No chequea el mimetype del fichero antes de procesarlo."))
    parser.add_option('-a', '--absolute', action="store_true",
        dest='absolute', default=False, 
        help=_(u"Muestra el camino absoluto de los archivos y no el relativo."))
    parser.add_option('', '--show-detectors', action="store_true",
        dest='show_detectors', default=False, 
        help=_(u"Muestra los detectores disponibles."))
    parser.add_option('', '--hide_encoding', action="store_true",
        dest='hide_encoding', default=False, 
        help=_(u"No mostrar las codificaciones detectadas (solo los caminos) ."))
    parser.add_option('-d', '--detector', action="store",
        dest='detector', default='check', 
        choices=[e.name for e in pkg_resources.iter_entry_points('charset.detectors')],
        help=_(u"Selecciona el detector que se utilizará (por defecto: check)."))
    
    def __init__(self):
        self._ms = None
        options, args = self.parser.parse_args()
        self._encoding = options.encoding
        self._absolute = options.absolute
        self._mimetype = not options.no_mimetype
        self._show_detectors = options.show_detectors
        self._hide_encoding = options.hide_encoding
        
        data = None
        for entry in pkg_resources.iter_entry_points('charset.detectors'):
            if entry.name == options.detector:
                data = entry.load()
                break
        if inspect.isclass(data):
            self._detector = data()
        elif callable(data):
            self._detector = data
        else:
            raise RuntimeError("Wrong detector registered")
        self._path = args[0] if args else None
        if self._mimetype:
            self._ms = magic.open(magic.MAGIC_MIME_TYPE)
            self._ms.load()
        
    def show_detectors(self):
        it = pkg_resources.iter_entry_points('charset.detectors')
        detectors = [entry.name for entry in it]
        print _("Detectores disponibles:"), ", ".join(detectors)
    
    def show_processed(self, path, encoding):
        if self._absolute:
            path = os.path.abspath(path)
        if self._hide_encoding:
            print path
        else:
            print path, "(%s)" % encoding
    
    def process_file(self, path):
        assert os.path.isfile(path), "El camino debe ser un fichero."
        if self._absolute:
            path = os.path.abspath(path)
        if self._mimetype:
            mimetype = self._ms.file(path)
            if not mimetype.startswith('text/'):
                self.show_processed(path, "WRONG_FORMAT")
                return
        text = open(path).read()
        try:
            encoding = self._detector.detect(text)
        except ValueError:
            self.show_processed(path, "UNKNOWN_ENCODING")
            return
        try:
            if self._encoding and self._encoding != encoding:
                text = text.decode(encoding)
                text = text.encode(self._encoding)
                open(path, 'w').write(text)
        except UnicodeDecodeError:
            self.show_processed(path, "UNKNOWN_ENCODING")
            return
        self.show_processed(path, encoding)
        
    def process_directory(self, path):
        assert os.path.isdir(path), "El camino debe ser un directorio."
        for path, dirs, files in os.walk(path):
            files.sort()
            for filename in files:
                self.process_file(os.path.join(path, filename))
    
    def __call__(self):
        if not self._show_detectors and not self._path:
            processed = False
            try:
                while True:
                    path = raw_input()
                    path = path.strip()
                    self.process_file(path)
                    processed = True
            except EOFError:
                pass
            if not processed:
                self.parser.error(
                    _(u"Debe especificar el camino de un fichero o directorio."))
        if self._show_detectors:
            self.show_detectors()
        if self._path:
            if not os.path.exists(self._path):
                self.parser.error(_(u"El camino no existe."))
            if os.path.isfile(self._path):
                self.process_file(self._path)
            else:
                self.process_directory(self._path)
        
    @classmethod
    def run(cls):
        app = cls()
        app()
    
    

