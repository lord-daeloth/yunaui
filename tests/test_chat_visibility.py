"""Exercise the real chat panel drawing path with a minimal ImGui stub."""
from pathlib import Path
import unittest
from lupa.luajit21 import LuaRuntime

SOURCE = (Path(__file__).resolve().parents[1] / 'yunaui.lua').read_text(encoding='utf-8')
START = SOURCE.index('function C.chat_chain()')
PANEL = SOURCE[START:SOURCE.index('        st.vis_n = 0;', START)] + '\n    end\nend\nreturn draw_chat'

class ChatVisibility(unittest.TestCase):
    def panel(self, n, fade, used=0, hover=False, look='clear', linked=False, vertical=False, window_fade=None, third_link=False):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            cfg = { chat=true, chat_split=true, chat3=true, cm_v1=true,
                chat_x=10, chat_y=400, chat_w=620, chat_h=260,
                chat2_x=640, chat2_y=400, chat2_w=620, chat2_h=260,
                chat3_x=10, chat3_y=100, chat3_w=460, chat3_h=260 };
            cw = {{scroll=0,hv=0},{scroll=0,hv=0},{scroll=0,hv=0}};
            logs = {{},{}}; legacy = {pad={}}; WATCH = {move=0}; CHATFLAGS=0;
            C = {rall=15, GOLDH2={1,.9,.6}}; ALLY = {};
            function C.screen() return 1920,1080 end
            ALLY.screen=C.screen;
            function C.clear_on() return look ~= 'classic' end
            function C.amb_alpha() return .5 end
            function typing_now() return nil end
            function save() end
            function U4(...) return {...} end
            function C.soft_ground(dl,x,y,w,h) panel={x=x,y=y,w=w,h=h} end
            DL = {};
            function DL.RF(dl,x,y,x1,y1) panel={x=x,y=y,w=x1-x,h=y1-y} end
            function DL.RFM() end
            function DL.L() end
            drawlist = {};
            function drawlist:AddConvexPolyFilled(pts)
                local top,bottom=math.huge,-math.huge
                for _,p in ipairs(pts) do top=math.min(top,p[2]); bottom=math.max(bottom,p[2]) end
                panel={y=top,h=bottom-top}
            end
            imgui = {};
            function imgui.SetNextWindowPos(p) pos=p end
            function imgui.SetNextWindowSize(s) size=s end
            function imgui.PushStyleVar() end
            function imgui.Begin() return true end
            function imgui.GetWindowPos() return pos[1],pos[2] end
            function imgui.GetWindowSize() return size[1],size[2] end
            function imgui.GetWindowDrawList() return drawlist end
            function imgui.IsWindowHovered() return hover end
            function imgui.IsWindowFocused() return false end
            function imgui.IsMouseDown() return false end
            function imgui.GetIO() return {DeltaTime=.016} end
            ImGuiWindowFlags_NoMove=0;
        ''')
        g = lua.globals()
        g.cfg.chat_fade_old = fade
        g.cfg.chat_link = linked
        g.cfg.chat_link_v = vertical
        g.cfg.chat3_link = third_link
        if window_fade is not None:
            g.cfg['chat_fade_w' + str(n)] = window_fade
        g.hover, g.look, g.YUI_HEX = hover, look, look == 'gold'
        for i in range(1, 4):
            g.cw[i].used_h = used
        lua.execute(PANEL)(n)
        return g.panel, g.cw[n].hv, g.pos[2], g.size[2]

    def test_fade_off_full_height_immediately_for_all_windows(self):
        for n in (1,2,3):
            for used in (0,20,260):
                for look in ('clear','classic','gold'):
                    with self.subTest(window=n, used=used, look=look):
                        panel,hv,y,h = self.panel(n,False,used,look=look)
                        self.assertEqual(hv,1)
                        self.assertIsNotNone(panel)
                        self.assertEqual(panel.y,y)
                        self.assertEqual(panel.h,h)

    def test_empty_linked_windows_are_visible_without_hover(self):
        for n in (1,2):
            for vertical in (False,True):
                panel,hv,y,h = self.panel(n,False,linked=True,vertical=vertical)
                self.assertEqual(panel.y,y)
                self.assertEqual(panel.h,h)

    def test_fade_on_still_hides_empty_and_shrinks_sparse_windows(self):
        for n in (1,2,3):
            panel,hv,_,_ = self.panel(n,True)
            self.assertIsNone(panel)
            self.assertEqual(hv,0)
            panel,hv,_,h = self.panel(n,True,20)
            self.assertLess(panel.h,h)

    def test_individual_fade_off_keeps_each_window_open(self):
        for n in (1,2,3):
            panel,hv,y,h = self.panel(n,True,window_fade=False)
            self.assertEqual(hv,1)
            self.assertEqual(panel.y,y)
            self.assertEqual(panel.h,h)

    def test_joined_third_window_stays_open_when_empty(self):
        for n in (1,2,3):
            panel,hv,y,h = self.panel(n,False,linked=True,third_link=True)
            self.assertEqual(panel.y,y)
            self.assertEqual(panel.h,h)

    def test_hover_still_expands_when_fade_is_on(self):
        panel,hv,_,_ = self.panel(2,True,hover=True)
        self.assertIsNotNone(panel)
        self.assertGreater(hv,0)

if __name__ == '__main__':
    unittest.main()
