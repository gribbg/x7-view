import sys
import tkinter as tk
import re
# noinspection PyPackageRequirements
from PIL import Image, ImageDraw

# Results:
"""
platform: win32
windowingsystem: win32
cursors [88]: X_cursor, arrow, based_arrow_down, based_arrow_up, boat, bogosity, bottom_left_corner, bottom_right_corner, bottom_side, bottom_tee, box_spiral, center_ptr, circle, clock, coffee_mug, cross, cross_reverse, crosshair, diamond_cross, dot, dotbox, double_arrow, draft_large, draft_small, draped_box, exchange, fleur, gobbler, gumby, hand1, hand2, heart, ibeam, icon, iron_cross, left_ptr, left_side, left_tee, leftbutton, ll_angle, lr_angle, man, middlebutton, mouse, no, none, pencil, pirate, plus, question_arrow, right_ptr, right_side, right_tee, rightbutton, rtl_logo, sailboat, sb_down_arrow, sb_h_double_arrow, sb_left_arrow, sb_right_arrow, sb_up_arrow, sb_v_double_arrow, shuttle, size, size_ne_sw, size_ns, size_nw_se, size_we, sizing, spider, spraycan, star, starting, target, tcross, top_left_arrow, top_left_corner, top_right_corner, top_side, top_tee, trek, ul_angle, umbrella, uparrow, ur_angle, wait, watch, xterm

platform: linux
windowingsystem: x11
cursors [78]: X_cursor, arrow, based_arrow_down, based_arrow_up, boat, bogosity, bottom_left_corner, bottom_right_corner, bottom_side, bottom_tee, box_spiral, center_ptr, circle, clock, coffee_mug, cross, cross_reverse, crosshair, diamond_cross, dot, dotbox, double_arrow, draft_large, draft_small, draped_box, exchange, fleur, gobbler, gumby, hand1, hand2, heart, icon, iron_cross, left_ptr, left_side, left_tee, leftbutton, ll_angle, lr_angle, man, middlebutton, mouse, none, pencil, pirate, plus, question_arrow, right_ptr, right_side, right_tee, rightbutton, rtl_logo, sailboat, sb_down_arrow, sb_h_double_arrow, sb_left_arrow, sb_right_arrow, sb_up_arrow, sb_v_double_arrow, shuttle, sizing, spider, spraycan, star, target, tcross, top_left_arrow, top_left_corner, top_right_corner, top_side, top_tee, trek, ul_angle, umbrella, ur_angle, watch, xterm

"""     # noqa


# Cursors data taken from tcltk source code:
# tcltk/tk/macosx/tkMacOSXCursor.c
# tcltk/tk/win/tkWinCursor.c
# tcltk/tk/unix/tkUnixCursor.c

pat = re.compile(r'^.*"([^"]*)".*$')


def names(raw):
    if isinstance(raw, list):
        return raw
    elif 'mouse cursors available in Tk' in raw:
        result = []
        for l in raw.splitlines():
            l = l.strip()
            if l and ' ' not in l and l != 'Windows' and not l.isupper():
                result.append(l)
        return result
    else:
        result = []
        for l in raw.splitlines():
            if not l.startswith('//'):
                if m := pat.match(l):
                    result.append(m.group(1))
        return result


def show_names():
    print('CURSORS_WINDOWS=', names(CURSORS_WINDOWS))
    print('CURSORS_MACOS=', names(CURSORS_MACOS))
    print('CURSORS_UNIX=', names(CURSORS_UNIX))


def make():
    image = Image.new('RGBA', (32, 32), '#00000000')
    draw = ImageDraw.ImageDraw(image)
    draw.line([0, 0, 10, 10], fill='red')
    draw.line([30, 0, 10, 10], fill='green')
    draw.line([0, 30, 10, 10], fill='blue')
    image.convert('1').save('test_cursor.xbm')
    # image.show(); import time; time.sleep(1)


def single():
    root = tk.Tk()
    # root.configure(cursor=('@/usr/include/X11/bitmaps/star', '/usr/include/X11/bitmaps/starMask', 'green', 'white'))
    # root.configure(cursor=('@/usr/include/X11/bitmaps/star', 'green'))
    # root.configure(cursor=('@/temp/test_cursor', '/tmp/test_cursor', 'black', 'white'))
    # root.configure(cursor=('@/tmp/test_cursor', 'red'))
    # root.configure(cursor=('@/temp/star', 'red'))
    root.configure(cursor=('@/temp/cursor98.cur', 'red', 'green'))
    root.mainloop()


def main():
    # single(); return
    # make()
    root = tk.Tk()
    all_names = [names(v) for v in [CURSORS_WINDOWS, CURSORS_MACOS, CURSORS_UNIX, CURSORS_TCL_LANG, CURSORS_TCL_TK_MAN]]
    raw = list(sorted(set(n for a in all_names for n in a)))
    cols = len(names(raw)) // 10
    good = []
    # raw.insert(0, r'@\temp\cursor98.cur')
    # raw.insert(0, r'@\temp\test_cursor.xbm')
    for n, name in enumerate(names(raw)):
        try:
            lbl = tk.Label(root, text=name, cursor=name, border=2, relief=tk.SOLID)
            good.append(name)
        except tk.TclError as err:
            print(name, ': ', err)
            lbl = tk.Label(root, text=name, border=2, relief=tk.GROOVE, fg='grey')
        lbl.grid(row=10+n % cols, column=n // cols, ipadx=2, ipady=2, padx=6, pady=2, sticky='news')

    print('platform:', sys.platform)
    print('windowingsystem:', root.tk.call('tk', 'windowingsystem'))
    print('cursors [%d]:' % len(good), ', '.join(good))
    lbl = tk.Label(root, text='Platform: %s    Windowing System: %s    Cursors: %d of %d' %
                              (sys.platform, root.tk.call('tk', 'windowingsystem'), len(good), len(names(raw))))
    lbl.grid(row=0, column=0, columnspan=cols, pady=2, ipady=2, sticky='news')

    root.mainloop()


# from https://wiki.tcl-lang.org/page/cursors
CURSORS_TCL_LANG = """
    arrow based_arrow_down based_arrow_up boat bogosity
    bottom_left_corner bottom_right_corner bottom_side bottom_tee
    box_spiral center_ptr circle clock coffee_mug cross cross_reverse
    crosshair diamond_cross dot dotbox double_arrow draft_large
    draft_small draped_box exchange fleur gobbler gumby hand1
    hand2 heart icon iron_cross left_ptr left_side left_tee leftbutton
    ll_angle lr_angle man middlebutton mouse pencil pirate plus
    question_arrow right_ptr right_side right_tee rightbutton rtl_logo
    sailboat sb_down_arrow sb_h_double_arrow sb_left_arrow
    sb_right_arrow sb_up_arrow sb_v_double_arrow shuttle sizing
    spider spraycan star target tcross top_left_arrow top_left_corner
    top_right_corner top_side top_tee trek ul_angle umbrella ur_angle
    watch X_cursor xterm
""".split()

# from http://www.tcl.tk/man/tcl8.4/TkCmd/cursors.htm
CURSORS_TCL_TK_MAN = """
NAME
cursors - mouse cursors available in Tk
DESCRIPTION
The -cursor widget option allows a Tk programmer to change the mouse cursor for a particular widget. The cursor names recognized by Tk on all platforms are:
X_cursor
arrow
based_arrow_down
based_arrow_up
boat
bogosity
bottom_left_corner
bottom_right_corner
bottom_side
bottom_tee
box_spiral
center_ptr
circle
clock
coffee_mug
cross
cross_reverse
crosshair
diamond_cross
dot
dotbox
double_arrow
draft_large
draft_small
draped_box
exchange
fleur
gobbler
gumby
hand1
hand2
heart
icon
iron_cross
left_ptr
left_side
left_tee
leftbutton
ll_angle
lr_angle
man
middlebutton
mouse
pencil
pirate
plus
question_arrow
right_ptr
right_side
right_tee
rightbutton
rtl_logo
sailboat
sb_down_arrow
sb_h_double_arrow
sb_left_arrow
sb_right_arrow
sb_up_arrow
sb_v_double_arrow
shuttle
sizing
spider
spraycan
star
target
tcross
top_left_arrow
top_left_corner
top_right_corner
top_side
top_tee
trek
ul_angle
umbrella
ur_angle
watch
xterm
PORTABILITY ISSUES
Windows
On Windows systems, the following cursors are mapped to native cursors:
arrow
center_ptr
crosshair
fleur
ibeam
icon
sb_h_double_arrow
sb_v_double_arrow
watch
xterm
And the following additional cursors are available:
no
starting
size
size_ne_sw
size_ns
size_nw_se
size_we
uparrow
wait
The no cursor can be specified to eliminate the cursor.
Mac OS X
On Mac OS X systems, the following cursors are mapped to native cursors:
arrow
cross
crosshair
ibeam
plus
watch
xterm
And the following additional native cursors are available:
copyarrow
aliasarrow
contextualmenuarrow
text
cross-hair
closedhand
openhand
pointinghand
resizeleft
resizeright
resizeleftright
resizeup
resizedown
resizeupdown
none
notallowed
poof
countinguphand
countingdownhand
countingupanddownhand
spinning
"""

# noinspection SpellCheckingInspection
CURSORS_WINDOWS = """
    {"starting",		IDC_APPSTARTING},
    {"arrow",			IDC_ARROW},
    {"ibeam",			IDC_IBEAM},
    {"icon",			IDC_ICON},
    {"no",			IDC_NO},
    {"size",			IDC_SIZEALL},
    {"size_ne_sw",		IDC_SIZENESW},
    {"size_ns",			IDC_SIZENS},
    {"size_nw_se",		IDC_SIZENWSE},
    {"size_we",			IDC_SIZEWE},
    {"uparrow",			IDC_UPARROW},
    {"wait",			IDC_WAIT},
    {"crosshair",		IDC_CROSS},
    {"fleur",			IDC_SIZEALL},
    {"sb_v_double_arrow",	IDC_SIZENS},
    {"sb_h_double_arrow",	IDC_SIZEWE},
    {"center_ptr",		IDC_UPARROW},
    {"watch",			IDC_WAIT},
    {"xterm",			IDC_IBEAM},
    {"hand2",			IDC_HAND},
    {"question_arrow",		IDC_HELP},
"""

# noinspection SpellCheckingInspection
CURSORS_UNIX = """
    {"starting",		IDC_APPSTARTING},
    {"arrow",			IDC_ARROW},
    {"ibeam",			IDC_IBEAM},
    {"icon",			IDC_ICON},
    {"no",			IDC_NO},
    {"size",			IDC_SIZEALL},
    {"size_ne_sw",		IDC_SIZENESW},
    {"size_ns",			IDC_SIZENS},
    {"size_nw_se",		IDC_SIZENWSE},
    {"size_we",			IDC_SIZEWE},
    {"uparrow",			IDC_UPARROW},
    {"wait",			IDC_WAIT},
    {"crosshair",		IDC_CROSS},
    {"fleur",			IDC_SIZEALL},
    {"sb_v_double_arrow",	IDC_SIZENS},
    {"sb_h_double_arrow",	IDC_SIZEWE},
    {"center_ptr",		IDC_UPARROW},
    {"watch",			IDC_WAIT},
    {"xterm",			IDC_IBEAM},
    {"hand2",			IDC_HAND},
    {"question_arrow",		IDC_HELP},
"""

# noinspection SpellCheckingInspection
CURSORS_MACOS = """
    {"arrow",			SELECTOR,    @"arrowCursor", nil, {0, 0}},
    {"top_left_arrow",		SELECTOR,    @"arrowCursor", nil, {0, 0}},
    {"left_ptr",		SELECTOR,    @"arrowCursor", nil, {0, 0}},
    {"copyarrow",		SELECTOR,    @"dragCopyCursor", @"_copyDragCursor", {0, 0}},
    {"aliasarrow",		SELECTOR,    @"dragLinkCursor", @"_linkDragCursor", {0, 0}},
    {"contextualmenuarrow",	SELECTOR,    @"contextualMenuCursor", nil, {0, 0}},
    {"movearrow",		SELECTOR,    @"_moveCursor", nil, {0, 0}},
    {"ibeam",			SELECTOR,    @"IBeamCursor", nil, {0, 0}},
    {"text",			SELECTOR,    @"IBeamCursor", nil, {0, 0}},
    {"xterm",			SELECTOR,    @"IBeamCursor", nil, {0, 0}},
    {"cross",			SELECTOR,    @"crosshairCursor", nil, {0, 0}},
    {"crosshair",		SELECTOR,    @"crosshairCursor", nil, {0, 0}},
    {"cross-hair",		SELECTOR,    @"crosshairCursor", nil, {0, 0}},
    {"tcross",			SELECTOR,    @"crosshairCursor", nil, {0, 0}},
    {"hand",			SELECTOR,    @"openHandCursor", nil, {0, 0}},
    {"openhand",		SELECTOR,    @"openHandCursor", nil, {0, 0}},
    {"closedhand",		SELECTOR,    @"closedHandCursor", nil, {0, 0}},
    {"fist",			SELECTOR,    @"closedHandCursor", nil, {0, 0}},
    {"pointinghand",		SELECTOR,    @"pointingHandCursor", nil, {0, 0}},
    {"resize",			SELECTOR,    @"arrowCursor", nil, {0, 0}},
    {"resizeleft",		SELECTOR,    @"resizeLeftCursor", nil, {0, 0}},
    {"resizeright",		SELECTOR,    @"resizeRightCursor", nil, {0, 0}},
    {"resizeleftright",		SELECTOR,    @"resizeLeftRightCursor", nil, {0, 0}},
    {"resizeup",		SELECTOR,    @"resizeUpCursor", nil, {0, 0}},
    {"resizedown",		SELECTOR,    @"resizeDownCursor", nil, {0, 0}},
    {"resizeupdown",		SELECTOR,    @"resizeUpDownCursor", nil, {0, 0}},
    {"resizebottomleft",	SELECTOR,    @"_bottomLeftResizeCursor", nil, {0, 0}},
    {"resizetopleft",		SELECTOR,    @"_topLeftResizeCursor", nil, {0, 0}},
    {"resizebottomright",	SELECTOR,    @"_bottomRightResizeCursor", nil, {0, 0}},
    {"resizetopright",		SELECTOR,    @"_topRightResizeCursor", nil, {0, 0}},
    {"notallowed",		SELECTOR,    @"operationNotAllowedCursor", nil, {0, 0}},
    {"poof",			SELECTOR,    @"disappearingItemCursor", nil, {0, 0}},
    {"wait",			SELECTOR,    @"busyButClickableCursor", nil, {0, 0}},
    {"spinning",		SELECTOR,    @"busyButClickableCursor", nil, {0, 0}},
    {"countinguphand",		SELECTOR,    @"busyButClickableCursor", nil, {0, 0}},
    {"countingdownhand",	SELECTOR,    @"busyButClickableCursor", nil, {0, 0}},
    {"countingupanddownhand",	SELECTOR,    @"busyButClickableCursor", nil, {0, 0}},
    {"help",			IMAGENAMED,  @"NSHelpCursor", nil, {8, 8}},
//  {"hand",			IMAGEBITMAP, MacCursorData(hand), nil, {0, 0}},
    {"bucket",			IMAGEBITMAP, MacCursorData(bucket), nil, {0, 0}},
    {"cancel",			IMAGEBITMAP, MacCursorData(cancel), nil, {0, 0}},
//  {"resize",			IMAGEBITMAP, MacCursorData(resize), nil, {0, 0}},
    {"eyedrop",			IMAGEBITMAP, MacCursorData(eyedrop), nil, {0, 0}},
    {"eyedrop-full",		IMAGEBITMAP, MacCursorData(eyedrop_full), nil, {0, 0}},
    {"zoom-in",			IMAGEBITMAP, MacCursorData(zoom_in), nil, {0, 0}},
    {"zoom-out",		IMAGEBITMAP, MacCursorData(zoom_out), nil, {0, 0}},
    {"X_cursor",		IMAGEBITMAP, MacXCursorData(X_cursor), nil, {0, 0}},
//  {"arrow",			IMAGEBITMAP, MacXCursorData(arrow), nil, {0, 0}},
    {"based_arrow_down",	IMAGEBITMAP, MacXCursorData(based_arrow_down), nil, {0, 0}},
    {"based_arrow_up",		IMAGEBITMAP, MacXCursorData(based_arrow_up), nil, {0, 0}},
    {"boat",			IMAGEBITMAP, MacXCursorData(boat), nil, {0, 0}},
    {"bogosity",		IMAGEBITMAP, MacXCursorData(bogosity), nil, {0, 0}},
    {"bottom_left_corner",	IMAGEBITMAP, MacXCursorData(bottom_left_corner), nil, {0, 0}},
    {"bottom_right_corner",	IMAGEBITMAP, MacXCursorData(bottom_right_corner), nil, {0, 0}},
    {"bottom_side",		IMAGEBITMAP, MacXCursorData(bottom_side), nil, {0, 0}},
    {"bottom_tee",		IMAGEBITMAP, MacXCursorData(bottom_tee), nil, {0, 0}},
    {"box_spiral",		IMAGEBITMAP, MacXCursorData(box_spiral), nil, {0, 0}},
    {"center_ptr",		IMAGEBITMAP, MacXCursorData(center_ptr), nil, {0, 0}},
    {"circle",			IMAGEBITMAP, MacXCursorData(circle), nil, {0, 0}},
    {"clock",			IMAGEBITMAP, MacXCursorData(clock), nil, {0, 0}},
    {"coffee_mug",		IMAGEBITMAP, MacXCursorData(coffee_mug), nil, {0, 0}},
//  {"cross",			IMAGEBITMAP, MacXCursorData(cross), nil, {0, 0}},
    {"cross_reverse",		IMAGEBITMAP, MacXCursorData(cross_reverse), nil, {0, 0}},
//  {"crosshair",		IMAGEBITMAP, MacXCursorData(crosshair), nil, {0, 0}},
    {"diamond_cross",		IMAGEBITMAP, MacXCursorData(diamond_cross), nil, {0, 0}},
    {"dot",			IMAGEBITMAP, MacXCursorData(dot), nil, {0, 0}},
    {"dotbox",			IMAGEBITMAP, MacXCursorData(dotbox), nil, {0, 0}},
    {"double_arrow",		IMAGEBITMAP, MacXCursorData(double_arrow), nil, {0, 0}},
    {"draft_large",		IMAGEBITMAP, MacXCursorData(draft_large), nil, {0, 0}},
    {"draft_small",		IMAGEBITMAP, MacXCursorData(draft_small), nil, {0, 0}},
    {"draped_box",		IMAGEBITMAP, MacXCursorData(draped_box), nil, {0, 0}},
    {"exchange",		IMAGEBITMAP, MacXCursorData(exchange), nil, {0, 0}},
    {"fleur",			IMAGEBITMAP, MacXCursorData(fleur), nil, {0, 0}},
    {"gobbler",			IMAGEBITMAP, MacXCursorData(gobbler), nil, {0, 0}},
    {"gumby",			IMAGEBITMAP, MacXCursorData(gumby), nil, {0, 0}},
    {"hand1",			IMAGEBITMAP, MacXCursorData(hand1), nil, {0, 0}},
    {"hand2",			IMAGEBITMAP, MacXCursorData(hand2), nil, {0, 0}},
    {"heart",			IMAGEBITMAP, MacXCursorData(heart), nil, {0, 0}},
    {"icon",			IMAGEBITMAP, MacXCursorData(icon), nil, {0, 0}},
    {"iron_cross",		IMAGEBITMAP, MacXCursorData(iron_cross), nil, {0, 0}},
//  {"left_ptr",		IMAGEBITMAP, MacXCursorData(left_ptr), nil, {0, 0}},
    {"left_side",		IMAGEBITMAP, MacXCursorData(left_side), nil, {0, 0}},
    {"left_tee",		IMAGEBITMAP, MacXCursorData(left_tee), nil, {0, 0}},
    {"leftbutton",		IMAGEBITMAP, MacXCursorData(leftbutton), nil, {0, 0}},
    {"ll_angle",		IMAGEBITMAP, MacXCursorData(ll_angle), nil, {0, 0}},
    {"lr_angle",		IMAGEBITMAP, MacXCursorData(lr_angle), nil, {0, 0}},
    {"man",			IMAGEBITMAP, MacXCursorData(man), nil, {0, 0}},
    {"middlebutton",		IMAGEBITMAP, MacXCursorData(middlebutton), nil, {0, 0}},
    {"mouse",			IMAGEBITMAP, MacXCursorData(mouse), nil, {0, 0}},
    {"pencil",			IMAGEBITMAP, MacXCursorData(pencil), nil, {0, 0}},
    {"pirate",			IMAGEBITMAP, MacXCursorData(pirate), nil, {0, 0}},
    {"plus",			IMAGEBITMAP, MacXCursorData(plus), nil, {0, 0}},
    {"question_arrow",		IMAGEBITMAP, MacXCursorData(question_arrow), nil, {0, 0}},
    {"right_ptr",		IMAGEBITMAP, MacXCursorData(right_ptr), nil, {0, 0}},
    {"right_side",		IMAGEBITMAP, MacXCursorData(right_side), nil, {0, 0}},
    {"right_tee",		IMAGEBITMAP, MacXCursorData(right_tee), nil, {0, 0}},
    {"rightbutton",		IMAGEBITMAP, MacXCursorData(rightbutton), nil, {0, 0}},
    {"rtl_logo",		IMAGEBITMAP, MacXCursorData(rtl_logo), nil, {0, 0}},
    {"sailboat",		IMAGEBITMAP, MacXCursorData(sailboat), nil, {0, 0}},
    {"sb_down_arrow",		IMAGEBITMAP, MacXCursorData(sb_down_arrow), nil, {0, 0}},
    {"sb_h_double_arrow",	IMAGEBITMAP, MacXCursorData(sb_h_double_arrow), nil, {0, 0}},
    {"sb_left_arrow",		IMAGEBITMAP, MacXCursorData(sb_left_arrow), nil, {0, 0}},
    {"sb_right_arrow",		IMAGEBITMAP, MacXCursorData(sb_right_arrow), nil, {0, 0}},
    {"sb_up_arrow",		IMAGEBITMAP, MacXCursorData(sb_up_arrow), nil, {0, 0}},
    {"sb_v_double_arrow",	IMAGEBITMAP, MacXCursorData(sb_v_double_arrow), nil, {0, 0}},
    {"shuttle",			IMAGEBITMAP, MacXCursorData(shuttle), nil, {0, 0}},
    {"sizing",			IMAGEBITMAP, MacXCursorData(sizing), nil, {0, 0}},
    {"spider",			IMAGEBITMAP, MacXCursorData(spider), nil, {0, 0}},
    {"spraycan",		IMAGEBITMAP, MacXCursorData(spraycan), nil, {0, 0}},
    {"star",			IMAGEBITMAP, MacXCursorData(star), nil, {0, 0}},
    {"target",			IMAGEBITMAP, MacXCursorData(target), nil, {0, 0}},
//  {"tcross",			IMAGEBITMAP, MacXCursorData(tcross), nil, {0, 0}},
//  {"top_left_arrow",		IMAGEBITMAP, MacXCursorData(top_left_arrow), nil, {0, 0}},
    {"top_left_corner",		IMAGEBITMAP, MacXCursorData(top_left_corner), nil, {0, 0}},
    {"top_right_corner",	IMAGEBITMAP, MacXCursorData(top_right_corner), nil, {0, 0}},
    {"top_side",		IMAGEBITMAP, MacXCursorData(top_side), nil, {0, 0}},
    {"top_tee",			IMAGEBITMAP, MacXCursorData(top_tee), nil, {0, 0}},
    {"trek",			IMAGEBITMAP, MacXCursorData(trek), nil, {0, 0}},
    {"ul_angle",		IMAGEBITMAP, MacXCursorData(ul_angle), nil, {0, 0}},
    {"umbrella",		IMAGEBITMAP, MacXCursorData(umbrella), nil, {0, 0}},
    {"ur_angle",		IMAGEBITMAP, MacXCursorData(ur_angle), nil, {0, 0}},
    {"watch",			IMAGEBITMAP, MacXCursorData(watch), nil, {0, 0}},
//  {"xterm",			IMAGEBITMAP, MacXCursorData(xterm), nil, {0, 0}},
"""

if __name__ == '__main__':
    main()
