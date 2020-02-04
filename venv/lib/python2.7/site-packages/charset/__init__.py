# -*- coding: utf-8 -*-

"""
This file is part of the textextractor python package
Copyrighted by Karel Vedecia Ortiz <kverdecia@uci.cu, kverdecia@gmail.com>
License: MPL 2.0 (http://www.mozilla.org/MPL/2.0/)
"""


from charset.detector import Detector
from charset.detector import MozDetector
from charset.detector import CheckDetector
from chardet.utf8prober import UTF8Prober


def text_to_unicode(text, detector=None):
    """Devuelve la conversión a `unicode` del texto que se pasa por parámetro.
    
    :param text: Texto que se va a convertir.
    :type text: `str` o `unicode`
    :param detector: Detector de codificación de caracteres que se va a 
        utilizar. Si no se especifica ninguno se utilizará una instancia
        de `charset.detector.CheckDetector`.
    :type detector: `charset.detector.Detector`
    :return: Texto convertido a `unicode`.
    :rtype: `unicode`
    :raise TypeError: Si el parámetro `text` no es una cadena.
    """
    if text is None or isinstance(text, unicode):
        return text
    if detector is None:
        detector = CheckDetector()
    encoding = detector.detect(text)
    return text.decode(encoding)


def text_to_utf8(text, detector=None):
    """Devuelve la conversión a `utf-8` del texto que se pasa por parámetro.
    
    :param text: Texto que se va a convertir.
    :type text: `str` o `unicode`
    :param detector: Detector de codificación de caracteres que se va a 
        utilizar. Si no se especifica ninguno se utilizará una instancia
        de `charset.detector.CheckDetector`.
    :type detector: `charset.detector.Detector`
    :return: Texto convertido a `utf-8`.
    :rtype: `unicode`
    :raise TypeError: Si el parámetro `text` no es una cadena.
    """
    if text is None:
        return None
    if isinstance(text, unicode):
        return text.encode('utf-8')
    if detector is None:
        detector = CheckDetector()
    encoding = detector.detect(text)
    if encoding == 'utf-8':
        return text
    return text.decode(encoding).encode('utf-8')
    
    
    
    
