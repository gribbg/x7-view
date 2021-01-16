"""
    Platform specific code
"""

import sys
import os
import dataclasses


@dataclasses.dataclass
class PlatformConfig:
    ui_platform: str            # Unique name to be used for further platform specific tests
    context_button_id: int      # aka right-mouse-button
    link_cursor: str            # hand-like cursor to use for links
    window_body: str            # Default background for Entry fields
    frame_background: str       # Default background for empty Frame


if sys.platform == 'win32':
    PCFG = PlatformConfig(
        ui_platform='win32',
        context_button_id=3,
        link_cursor='hand2',
        window_body='cyan',
        frame_background='cyan',
    )
elif sys.platform == 'darwin':
    # TODO-consider root.tk.call('tk', 'windowingsystem')=='aqua'
    PCFG = PlatformConfig(
        ui_platform='darwin',
        context_button_id=2,
        link_cursor='pointinghand',
        window_body='systemWindowBody',
        frame_background='#eeeeee',         # What about dark mode?
    )
elif sys.platform == 'linux' and 'microsoft' in str(os.uname()).lower():
    PCFG = PlatformConfig(
        ui_platform='linux_wsl',
        context_button_id=3,
        link_cursor='hand2',
        window_body='#ffffff',      # from tcltk/tk/library/ttk/clamTheme.tcl, $colors(-lightest)
        frame_background='cyan',
    )
else:
    raise ValueError('Unknown platform: ' + sys.platform + '/' + str(os.uname()))
