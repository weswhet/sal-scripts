#!/usr/local/sal/Python.framework/Versions/3.8/bin/python3


import argparse
import dbm
import os
import re
import shelve
import sys
import urllib
from xml.etree import ElementTree


DBPATH = "/usr/local/sal/macmodelshelf"


try:
    macmodelshelf = shelve.open(DBPATH)
except dbm.error as exception:
    exit(f"Couldn't open macmodelshelf.db: {exception}")


def model_code(serial):
    if "serial" in serial.lower(): # Workaround for machines with dummy serial numbers.
        return None
    if len(serial) in (12, 13) and serial.startswith("S"): # Remove S prefix from scanned codes.
        serial = serial[1:]
    if len(serial) in (11, 12):
        return serial[8:].decode("ascii")
    return None


def lookup_mac_model_code_from_apple(model_code):
    try:
        f = urllib.urlopen(
            "http://support-sp.apple.com/sp/product?cc=%s&lang=en_US" % model_code, timeout=2)
        et = ElementTree.parse(f)
        return et.findtext("configCode").decode("utf-8")
    except:
        return None


CLEANUP_RES = [
    (re.compile(ur"inch ? "), u"inch, "),
    (re.compile(ur"  "), u" "),
]
def cleanup_model(model):
    for pattern, replacement in CLEANUP_RES:
        model = pattern.sub(replacement, model)
    return model


def model(code, cleanup=True):
    global macmodelshelf
    if code == None:
        return None
    code = code.upper()
    try:
        model = macmodelshelf[code]
    except KeyError:
        printerr8(u"Looking up %s from Apple" % code)
        model = lookup_mac_model_code_from_apple(code)
        if model:
            macmodelshelf[code] = model
    if cleanup and model:
        return cleanup_model(model)
    else:
        return model


def _dump(cleanup=True, format=u"json"):
    assert format in (u"python", u"json", u"markdown")
    def clean(model):
        if cleanup:
            return cleanup_model(model)
        else:
            return model
    items = macmodelshelf.keys()
    items.sort()
    items.sort(key=len)
    if format == u"python":
        print8(u"macmodelshelfdump = {")
        print8(u",\n".join([u'    "%s": "%s"' % (code, clean(macmodelshelf[code])) for code in items]))
        print8(u"}")
    elif format == u"json":
        print8(u"{")
        print8(u",\n".join([u'    "%s": "%s"' % (code, clean(macmodelshelf[code])) for code in items]))
        print8(u"}")
    elif format == u"markdown":
        print8(u"Code | Model")
        print8(u":--- | :---")
        print8(u"\n".join(u'`%s` | %s' % (code, clean(macmodelshelf[code])) for code in items))


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(u"-n", u"--no-cleanup", action=u"store_false",
                   dest=u"cleanup", help=u"Don't clean up model strings.")
    p.add_argument(u"code", help=u"Serial number or model code")
    args = p.parse_args([x.decode(u"utf-8") for x in argv[1:]])

    dump_format = {
        u"dump": u"python",
        u"dump-python": u"python",
        u"dump-json": u"json",
        u"dump-markdown": u"markdown",
    }
    if args.code in dump_format.keys():
        _dump(args.cleanup, dump_format[args.code])
        return 0

    if len(args.code) in (11, 12, 13):
        m = model(model_code(args.code), cleanup=args.cleanup)
    else:
        m = model(args.code, cleanup=args.cleanup)
    if m:
        print m
        return 0
    else:
        printerr8(u"Unknown model %s" % repr(args.code))
        return os.EX_UNAVAILABLE


if __name__ == '__main__':
    sys.exit(main(sys.argv))
