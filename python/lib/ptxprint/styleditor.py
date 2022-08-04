
import re, os
from ptxprint.usfmutils import Sheets
from ptxprint.font import FontRef
from ptxprint.utils import f2s, textocol, coltotex, coltoonemax, Path
from copy import deepcopy

mkrexceptions = {k.lower().title(): k for k in ('BaseLine', 'TextType', 'TextProperties', 'FontName',
                'FontSize', 'FirstLineIndent', 'LeftMargin', 'RightMargin',
                'SpaceBefore', 'SpaceAfter', 'CallerStyle', 'CallerRaise',
                'NoteCallerStyle', 'NoteCallerRaise', 'NoteBlendInto', 'LineSpacing',
                'StyleType', 'ColorName', 'XMLTag', 'TEStyleName', 'ztexFontFeatures', 'ztexFontGrSpace',
                'FgImage', 'FgImagePos', 'FgImageScale', 'BgImage', 'BgImageScale', 'BgImagePos', 'BgImageLow',
                'BgImageColour', 'BgImageColor', 'BgImageAlpha', 'BgImageOversize', 'BgColour', 'BgColor',
                'BorderWidth', 'BorderColour', 'BorderColor', 'BorderVPadding', 'BorderHPadding', 
                'BoxVPadding', 'BoxHPadding')}
binarymkrs = {"bold", "italic", "smallcaps"}

absolutes = {"baseline", "raise", "callerraise", "notecallerraise"}
aliases = {"q", "s", "mt", "to", "imt", "imte", "io", "iq", "is", "ili", "pi",
           "qm", "sd", "ms", "mt", "mte", "li", "lim", "liv", }
_defFields = {"Marker", "EndMarker", "Name", "Description", "OccursUnder", "TextProperties", "TextType", "StyleType"}

def asFloatPts(self, s, mrk=None, model=None):
    if mrk is None:
        mrk = self.marker
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(\D*?)\s*$", str(s))
    if m:
        try:
            v = float(m[1])
        except (TypeError, ValueError):
            v = 0.
        units = m[2]
        if units == "" or units.lower() == "pt" or mrk is None:
            return v
        elif units == "in":
            return v * 72.27
        elif units == "mm":
            return v * 72.27 / 25.4
        try:
            fsize = float(self.getval(mrk, "FontSize"))
        except TypeError:
            return v
        if fsize is None:
            return v
        try:
            bfsize = float(self.model.get("s_fontsize"))
        except TypeError:
            return v
        if units == "ex":
            return v * fsize / 12. / 2.
        elif units == "em":
            return v * fsize / 12.
        return v
    else:
        try:
            return float(s)
        except (ValueError, TypeError):
            return 0.

def toFloatPts(self, v, mrk=None, model=None):
    return "{} pt".format(f2s(float(v)))

def fromFloat(self, s, mrk=None, model=None):
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.

def toFloat(self, v, mrk=None, model=None):
    return f2s(float(v))

def from12(self, s, mrk=None, model=None):
    try:
        return float(s) / 12.
    except (TypeError, ValueError):
        return 0.

def to12(self, v, mrk=None, model=None):
    return f2s(float(v) * 12.)

def fromBool(self, s, mrk=None, model=None):
    return not(s is None or s is False or s == "-")

def toBool(self, v, mrk=None, model=None):
    return "" if v else "-"

def fromSet(self, s, mrk=None, model=None):
    if isinstance(s, set):
        return s
    return set(s.split())

def toSet(self, s, mrk=None, model=None):
    if isinstance(s, set):
        return " ".join(s)
    return s

def fromFont(self, s, mrk=None, model=None):
    if mrk is None:
        mrk = self.marker
    class Shim:
        def get(subself, key, default=None):
            if key == 'FontName':
                return self.sheet.get(mrk, {}).get(key,
                        self.basesheet.get(mrk, {}).get(key, default))
            return self.getval(mrk, key, default)
    return FontRef.fromTeXStyle(Shim())

def toFont(self, v, mrk=None, model=None):
    if v is None:
        return
    if mrk is None:
        mrk = self.marker
    class Shim:
        def __setitem__(subself, key, val):
            if key == 'FontName':
                self.sheet.setdefault(mrk, {})[key] = val
            else:
                self.setval(mrk, key, val)
        def __contains__(subself, key):
            return self.haskey(mrk, key)
        def __delitem__(subself, key):
            return self.sheet.get(mrk, {}).pop(key, None)
        def pop(subself, key, dflt):
            return self.sheet.get(mrk, {}).pop(key, dflt)
    regularfont = model.get("bl_fontR")
    oldfont = self.basesheet.get(mrk, {}).get("FontName", None)
    return v.updateTeXStyle(Shim(), regular=regularfont, force=oldfont is not None)

def fromOneMax(self, v, mrk=None, model=None):
    res = coltotex(textocol(v))
    # print(f"FROM: {mrk=} {v=} {res=}")
    return res

def toOneMax(self, v, mrk=None, model=None):
    res = " ".join("{:.2f}".format(x) for x in coltoonemax(textocol(v)))
    # print(f"TO: {mrk=} {v=} {res=}")
    return res

def fromFileName(self, v, mrk=None, model=None):
    if model is not None:
        rpath = model.configPath()
        return os.path.abspath(os.path.relpath(v, rpath))
    else:
        return v

def toFileName(self, v, mrk=None, model=None):
    return v

_fieldmap = {
    'bold':             (fromBool, toBool),
    'italic':           (fromBool, toBool),
    'superscript':      (fromBool, toBool),
    'smallcaps':        (fromBool, toBool),
    'firstlineindent':  (fromFloat, toFloat),
    'leftmargin':       (fromFloat, toFloat),
    'rightmargin':      (fromFloat, toFloat),
    'linespacing':      (fromFloat, toFloat),
    'raise':            (asFloatPts, toFloatPts),
    'baseline':         (asFloatPts, toFloatPts),
    'callerraise':      (asFloatPts, toFloatPts),
    'notecallerraise':  (asFloatPts, toFloatPts),
    'fontsize':         (from12, to12),
    'spacebefore':      (from12, to12),
    'spaceafter':       (from12, to12),
    'fontname':         (fromFont, toFont),
    'textproperties':   (fromSet, toSet),
    'occursunder':      (fromSet, toSet),
    'bordercolor':      (fromOneMax, toOneMax),
    'bgimagecolor':     (fromOneMax, toOneMax),
    'bgcolor':          (fromOneMax, toOneMax),
    'bgimage':          (fromFileName, toFileName),
    'fgimage':          (fromFileName, toFileName)
}

class StyleEditor:

    def __init__(self, model):
        self.model = model
        self.sheet = None
        self.basesheet = None
        self.marker = None
        self.registers = {}

    def copy(self):
        res = self.__class__(self.model)
        res.sheet = Sheets(base=self.sheet)
        res.basesheet = Sheets(base=self.basesheet)
        res.marker = self.marker
        res.registers = dict(self.registers)
        return res

    def allStyles(self):
        if self.sheet is None:
            return {}
        res = set(self.basesheet.keys())
        res.update(self.sheet.keys())
        return res

    def allValueKeys(self, m):
        res = set(self.basesheet.get(m, {}).keys())
        res.update(self.sheet.get(m, {}).keys())
        return res

    def asStyle(self, m):
        if m is None:
            res = {}
            for m in self.allStyles():
                res[m] = {str(k):v for k, v in self.basesheet.get(m, {}).items()}
                res[m].update({str(k):v for k, v in self.sheet.get(m, {}).items()})
        else:
            res = {str(k):v for k, v in self.basesheet.get(m, {}).items()}
            res.update({str(k):v for k, v in self.sheet.get(m, {}).items()})
        return res

    def getval(self, mrk, key, default=None, baseonly=False):
        if self.sheet is None:
            raise KeyError(f"stylesheet missing: {mrk} + {key}")
        res = self.sheet.get(mrk, {}).get(key, None) if not baseonly else None
        if res is None or (mrk in _defFields and not len(res)):
            res = self.basesheet.get(mrk, {}).get(key, default)
        if key.lower() in _fieldmap and res is not None:
            res = _fieldmap[key.lower()][0](self, res, mrk=mrk, model=self.model)
        return res

    def setval(self, mrk, key, val, ifunchanged=False):
        if self.sheet is None:
            raise KeyError(f"{mrk} + {key}")
        if ifunchanged and self.basesheet.get(mrk, {}).get(key, None) != \
                self.sheet.get(mrk, {}).get(key, None):
            return
        if val is not None and key.lower() in _fieldmap:
            newval = _fieldmap[key.lower()][1](self, val, mrk=mrk, model=self.model)
            if newval is None and val is not None:
                return      # Probably a font which has edited the object for us
            else:
                val = newval
        if key in self.sheet.get(mrk, {}) and (val is None or val == self.basesheet.get(mrk, {}).get(key, None)):
            del self.sheet[mrk][key]
            return
        elif self.basesheet.get(mrk, {}).get(key, None) != val and val is not None:
            self.sheet.setdefault(mrk, {})[key] = val or ""
        elif key in self.basesheet.get(mrk, {}) and val is None:
            del self.basesheet[mrk][key]

    def haskey(self, mrk, key):
        if self.sheet is None:
            raise KeyError(f"stylesheet missing: {mrk} + {key}")
        if key in self.sheet.get(mrk, {}) or key in self.basesheet.get(mrk, {}):
            return True
        return False

    def get_font(self, mrk, style=""):
        f = self.getval(mrk, " font")
        if f is not None:
            return f
        f = self.model.getFont(style if len(style) else "regular")
        return f

    def load(self, sheetfiles):
        if len(sheetfiles) == 0:
            return
        foundp = False
        self.basesheet = Sheets(sheetfiles[:-1])
        self.sheet = Sheets(sheetfiles[-1:], base = "")

    def _convertabs(self, key, val):
        baseline = float(self.model.get("s_linespacing", 1.))
        if key.lower() == "baseline":
            return val * baseline
        elif key.lower() == "linespacing":
            return val / baseline
        return val

    def _eq_val(self, a, b, key=""):
        if key.lower() in absolutes:
            fa = asFloatPts(self, str(a))
            fb = asFloatPts(self, str(b))
            return fa == fb
        else:
            try:
                fa = float(a)
                fb = float(b)
                return abs(fa - fb) < 0.005
            except (ValueError, TypeError):
                pass
            if key.lower() not in binarymkrs:
                a = a or ""
                b = b or ""
            return a == b

    def _str_val(self, v, key=""):
        if isinstance(v, (set, list)):
            if key.lower() == "textproperties":
                res = " ".join(x.lower() if x else "" for x in sorted(v))
            else:
                res = " ".join(self._str_val(x, key) for x in sorted(v))
        elif isinstance(v, float):
            res = f2s(v)
        else:
            res = str(v)
        return res

    def output_diffile(self, outfh, inArchive=False, sheet=None, basesheet=None):
        def normmkr(s):
            x = s.lower().title()
            return mkrexceptions.get(x, x)
        if basesheet is None:
            basesheet = self.basesheet
        if sheet is None:
            sheet = self.sheet
        for m in sorted(self.allStyles()):
            markerout = False
            if m in aliases:
                sm = self.asStyle(m+"1")
            elif inArchive:
                sm = sheet.get(m, {}).copy()
            else:
                sm = sheet.get(m, {})
            om = basesheet.get(m, {})
            if 'zDerived' in om or 'zDerived' in sm:
                continue
            for k, v in sm.items():
                if k.startswith(" "):
                    continue
                other = om.get(k, None)
                if not self._eq_val(other, v, key=k):
                    if not markerout:
                        outfh.write("\n\\Marker {}\n".format(m))
                        markerout = True
                    outfh.write("\\{} {}\n".format(normmkr(k), self._str_val(v, k)))

    def merge(self, basese, newse):
        for m in newse.sheet.keys():
            allkeys = newse.allValueKeys(m)
            allkeys.update(basese.allValueKeys(m))
            allkeys.update(self.allValueKeys(m))
            for k in allkeys:
                nv = newse.getval(m, k)
                bv = basese.getval(m, k)
                sv = self.getval(m, k)
                if sv != bv:
                    continue
                if nv != bv:
                    self.setval(m, k, nv)
