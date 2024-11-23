#!/usr/bin/python3

import re
from ptxprint.utils import bookcodes, _allbkmap, refSort, _hebOrder
from ptxprint.unicode.ducet import get_sortkey, SHIFTTRIM, tailored
import logging

logger = logging.getLogger(__name__)

bkranges = {'ot':   ([b for b, i in _allbkmap.items() if 1  < i < 41], True),
            'nt':   ([b for b, i in _allbkmap.items() if 60 < i < 88], True),
            'dc':   ([b for b, i in _allbkmap.items() if 40 < i < 61], True),
            'pre':  ([b for b, i in _allbkmap.items() if 0 <= i < 2], False),
            'post': ([b for b, i in _allbkmap.items() if 87 < i], False),
            'heb':  (_hebOrder, True),
            'bible': ([b for b, i in _allbkmap.items() if 1 < i < 88], True)}

def sortToC(toc, bksorted):
    if bksorted:
        bksrt = lambda b: refSort(b[0])
    else:
        bksrt = lambda b: int(b[-1])
    # bknums = {k:i for i,k in enumerate(booklist)}
    return sorted(toc, key=bksrt)

def generateTex(alltocs):
    res = []
    for k, v in alltocs.items():
        res.append(r"\defTOC{{{}}}{{".format(k))
        for e in v:
            res.append(r"\doTOCline"+"".join("{"+s+"}" for s in e))
        res.append("}")
    return "\n".join(res)

class TOC:
    def __init__(self, infname):
        mode = 0
        self.tocentries = []
        self.sides = set()
        with open(infname, encoding="utf-8") as inf:
            for l in inf.readlines():
                logger.debug("TOCline: {}".format(l.strip()))
                if mode == 0 and re.match(r"\\defTOC\{main\}", l):
                    mode = 1
                elif mode == 1:
                    m = re.match(r"\\doTOCline\{(.*)\}\{(.*)\}\{(.*)\}\{(.*)\}\{(.*)\}", l)
                    if m:
                        self.tocentries.append(list(m.groups()))
                        if m.group(1)[3:] != "":
                            self.sides.add(m.group(1)[3:])
                    elif l.startswith("}"):
                        mode = 0
                        break

    def createtocvariants(self, booklist, ducet=None):
        res = {}
        for s in list(self.sides) + [""]:
            tocentries = [t for t in self.tocentries if s == "" or t[0][3:] == s]
            res['main' + s] = sortToC(self.fillEmpties(tocentries[:]), False)  # sort in page order
            for k, r in bkranges.items():
                ttoc = []
                for e in tocentries:
                    try:
                        if e[0][:3] in r[0]:
                            ttoc.append(e[:])
                    except ValueError:
                        pass
                        
                res[k+s] = sortToC(self.fillEmpties(ttoc), r[1])
            for i in range(3):
                if i == 2:
                    ducet = tailored("&[first primary ignorable] << 0 << 1 << 2 << 3 << 4 << 5 << 6 << 7 << 8 << 9", ducet)
                def makekey(txt):
                    return int(txt) if txt.isdigit() else get_sortkey(txt, variable=SHIFTTRIM, ducet=ducet)
                def naturalkey(txt):
                    return [makekey(c) for c in reversed(re.split(r'(\d+)', txt))]
                for a in (("sort", tocentries), ("bib", res["bible"+s])):
                    ttoc = []
                    k = a[0]+chr(97+i)+s
                    res[k] = ttoc
                    for e in sorted(self.fillEmpties(a[1][:]), key=lambda x:naturalkey(x[i+1])):
                        ttoc.append(e)
        return res

    def fillEmpties(self, ttoc):
        if len(ttoc):
            tcols = [False] * len(ttoc[0])
            for t in ttoc:
                for i, e in enumerate(t):
                    if len(e):
                        tcols[i] = True
            for t in ttoc:
                for i, e in enumerate(t):
                    if not len(e) and tcols[i]:
                        t[i] = "\\kern-3pt"
        return ttoc
