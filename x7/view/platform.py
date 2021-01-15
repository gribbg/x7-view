"""
    Platform specific code
"""

import sys
import os
import dataclasses


@dataclasses.dataclass
class PlatformConfig:
    ui_platform: str
    context_button_id: int
    link_cursor: str
    window_body: str


if sys.platform == 'win32':
    PCFG = PlatformConfig(
        ui_platform='win32',
        context_button_id=3,
        link_cursor='hand2',
        window_body='cyan',
    )
elif sys.platform == 'darwin':
    # TODO-consider root.tk.call('tk', 'windowingsystem')=='aqua'
    PCFG = PlatformConfig(
        ui_platform='darwin',
        context_button_id=2,
        link_cursor='pointinghand',
        window_body='systemWindowBody',
    )
elif sys.platform == 'linux' and 'microsoft' in str(os.uname()).lower():
    PCFG = PlatformConfig(
        ui_platform='linux_wsl',
        context_button_id=3,
        link_cursor='hand2',
        window_body='#ffffff',      # from tcltk/tk/library/ttk/clamTheme.tcl, $colors(-lightest)
    )
else:
    raise ValueError('Unknown platform: ' + sys.platform + '/' + str(os.uname()))
