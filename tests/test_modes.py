"""Mode regression checks. Requires lupa (LuaJIT 2.1): python -m unittest discover -s tests."""
from pathlib import Path
import unittest
from lupa.luajit21 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'yunaui.lua').read_text(encoding='utf-8')

def section(start, end):
    return SOURCE[SOURCE.index(start):SOURCE.index(end, SOURCE.index(start))]

class Modes(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            C = {}; cfg = { target_fx = 'blade', head_bars = 'fixed', target_x = 100, target_y = 80,
                chat_x = 20, chat_y = 30, golden_vex = false };
            FIGHT = { PIECES = {}, fx = {} }; ALLY = {}; WATCH = { move = 0 };
            PANEL = { GOLD = {1,.76,.34}, GOLD2 = {1,.9,.62} };
            NEON = {}; NEON2 = {}; C.acc = {};
            C.HPCOL = { pink = {{1,.5,.8},{.8,.2,.8},{1,.4,.7}} };
            C.HEXHP = {{1,.8,.4},{.8,.5,.1},{1,.9,.6}};
            C.HEXMP = {{.3,.8,1},{.2,.5,1},{.5,.8,1}};
            C.MPCOL = {{.4,.5,1},{.6,.4,1},{.6,.6,1}};
            C.TGTCOL = { pink = {{1,.8,.9}} };
            C.hp2 = {.8,.3,1}; C.mp = {.4,.5,1}; C.mp2 = {.6,.4,1};
            function C.screen() return 1920,1080 end
            function save() end
            eq = { hpbar_x = 200, hpbar_y = 700, sb_anchor = true };
            function YUI_EQ_GET() return eq end
            function YUI_EQ_APPLY(t) for k,v in pairs(t) do eq[k]=v end end
            LAYOUT = {};
            function LAYOUT.capture() return {o={target_x=cfg.target_x,target_y=cfg.target_y},eq={hpbar_x=eq.hpbar_x,hpbar_y=eq.hpbar_y}} end
            function LAYOUT.apply(o,e) for k,v in pairs(o) do cfg[k]=v end; YUI_EQ_APPLY(e or {}) end
            EDIT = { G = { start = function() end } };
        ''')
        self.lua.execute(section('C.MODEKEYS =', 'C.GOLDH, C.GOLDH2'))
        self.lua.execute(section('function C.apply_hp()', '-- A thin black edge'))
        self.lua.execute(section('function C.head_bars_on()', 'function C.aggro()'))
        self.lua.execute(section('YUI_HIDE_STATBARS =', 'YUI_BAR_OVERLAY ='))
        self.lua.execute(section('C.MD =', 'function C.MD.draw()'))

    def test_all_files_compile(self):
        compile_lua = self.lua.eval('function(s) local f,e=loadstring(s); return f ~= nil,e end')
        for path in ROOT.glob('*.lua'):
            ok, error = compile_lua(path.read_text(encoding='utf-8'))
            self.assertTrue(ok, f'{path.name}: {error}')

    def test_three_modes_keep_independent_layouts(self):
        self.lua.execute('''
            C.setmode('golden');
            assert(C.mode()=='golden' and YUI_HEX and YUI_HP_COL==C.HEXHP);
            assert(cfg.target_x==100 and eq.hpbar_x==200);
            assert(not C.head_bars_on() and not YUI_HIDE_STATBARS());
            cfg.target_x=300; eq.hpbar_x=400;
            C.setmode(true);
            assert(C.mode()=='hex' and C.head_bars_on() and YUI_HIDE_STATBARS());
            cfg.target_x=500; eq.hpbar_x=600;
            C.setmode(false);
            assert(C.mode()=='vex' and not YUI_HEX and YUI_HP_COL==C.HPCOL.pink);
            assert(cfg.target_x==100 and eq.hpbar_x==200);
            C.setmode('golden');
            assert(cfg.target_x==300 and eq.hpbar_x==400 and not C.head_bars_on());
            C.setmode('hex'); assert(cfg.target_x==500 and eq.hpbar_x==600);
        ''')

    def test_golden_from_hex_uses_saved_vex_layout(self):
        self.lua.execute('''
            C.setmode('hex'); cfg.target_x=900; eq.hpbar_x=800;
            C.setmode('golden');
            assert(cfg.target_x==100 and eq.hpbar_x==200 and cfg.head_bars=='fixed');
        ''')

    def test_reload_theme_keeps_golden_bars_fixed(self):
        self.lua.execute('''
            C.setmode('golden'); YUI_HEX=nil; C.apply_hp();
            assert(YUI_HEX and cfg.head_bars=='fixed');
            assert(not YUI_HIDE_STATBARS() and not C.head_bars_on());
            assert(C.mpb1==C.HEXMP[1] and C.tgt1==C.HEXHP[3]);
        ''')

    def test_preview_cancel_and_pick_preserve_original(self):
        self.lua.execute('''
            C.setmode('golden'); cfg.target_x=330; eq.hpbar_x=440;
            C.MD.start(false);
            C.MD.mode='hex'; C.MD.link=true; C.MD.apply();
            assert(C.head_bars_on());
            C.MD.pick('golden');
            assert(C.mode()=='golden' and cfg.target_x==330 and eq.hpbar_x==440);
            C.MD.start(false); C.MD.mode='vex'; C.MD.link=false; C.MD.apply();
            C.MD.pick('vex');
            assert(C.mode()=='vex' and cfg.target_x==100 and eq.hpbar_x==200);
            C.setmode('golden'); assert(cfg.target_x==330 and eq.hpbar_x==440);
        ''')

    def test_interrupted_preview_restores_golden(self):
        self.lua.execute('''
            C.setmode('golden'); cfg.target_x=321;
            C.MD.start(false); C.MD.mode='hex'; C.MD.link=true; C.MD.apply();
            C.MD.restore(); C.apply_hp();
            assert(C.mode()=='golden' and cfg.target_x==321 and not C.head_bars_on());
        ''')

if __name__ == '__main__':
    unittest.main()
