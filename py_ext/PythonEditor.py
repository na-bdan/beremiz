import keyword
import wx.stc as stc

from controls.CustomStyledTextCtrl import faces
from editors.CodeFileEditor import CodeFileEditor, CodeEditor

class PythonCodeEditor(CodeEditor):

    KEYWORDS = keyword.kwlist
    COMMENT_HEADER = "##"
    
    def SetCodeLexer(self):
        self.SetLexer(stc.STC_LEX_PYTHON)
        
        # Line numbers in margin
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,'fore:#000000,back:#99A9C2,size:%(size)d' % faces)    
        # Highlighted brace
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,'fore:#00009D,back:#FFFF00,size:%(size)d' % faces)
        # Unmatched brace
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,'fore:#00009D,back:#FF0000,size:%(size)d' % faces)
        # Indentation guide
        self.StyleSetSpec(stc.STC_STYLE_INDENTGUIDE, 'fore:#CDCDCD,size:%(size)d' % faces)

        # Python styles
        self.StyleSetSpec(stc.STC_P_DEFAULT, 'fore:#000000,size:%(size)d' % faces)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE,  'fore:#008000,back:#F0FFF0,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, 'fore:#008000,back:#F0FFF0,size:%(size)d' % faces)
        # Numbers
        self.StyleSetSpec(stc.STC_P_NUMBER, 'fore:#008080,size:%(size)d' % faces)
        # Strings and characters
        self.StyleSetSpec(stc.STC_P_STRING, 'fore:#800080,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_P_CHARACTER, 'fore:#800080,size:%(size)d' % faces)
        # Keywords
        self.StyleSetSpec(stc.STC_P_WORD, 'fore:#000080,bold,size:%(size)d' % faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, 'fore:#800080,back:#FFFFEA,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, 'fore:#800080,back:#FFFFEA,size:%(size)d' % faces)
        # Class names
        self.StyleSetSpec(stc.STC_P_CLASSNAME, 'fore:#0000FF,bold,size:%(size)d' % faces)
        # Function names
        self.StyleSetSpec(stc.STC_P_DEFNAME, 'fore:#008080,bold,size:%(size)d' % faces)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, 'fore:#800000,bold,size:%(size)d' % faces)
        # Identifiers. I leave this as not bold because everything seems
        # to be an identifier if it doesn't match the above criterae
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, 'fore:#000000,size:%(size)d' % faces)
        

#-------------------------------------------------------------------------------
#                          CFileEditor Main Frame Class
#-------------------------------------------------------------------------------

class PythonEditor(CodeFileEditor):
    
    CONFNODEEDITOR_TABS = CodeFileEditor.CONFNODEEDITOR_TABS + [
        (_("Python code"), "_create_PythonCodeEditor")]
    
    def _create_PythonCodeEditor(self, prnt):
        self.PythonCodeEditor = PythonCodeEditor(prnt, self.ParentWindow, self.Controler)
        
        return self.PythonCodeEditor

    def RefreshView(self):
        CodeFileEditor.RefreshView(self)
        
        self.PythonCodeEditor.RefreshView()

    def Find(self, direction, search_params):
        self.PythonCodeEditor.Find(direction, search_params)
