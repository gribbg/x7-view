"""
modes: select, add, pan
need to be able to install top-level click handlers and update mode buttons
editing curve should set top-level hook
hook also needs to handle ESC to abort action in progress

select mode: install callbacks on all curves, hide cps
curve selected: remove curve cbs, show active cps
need curve edit done command


undo/redo:
    define Command() pattern
    and CommandStack()
"""


class Mode(object):
    name = 'name of mode'
    tag = 'select'  # action tag from mode buttons
    item = object  # item actively being edited, etc.

    def event_click(self, event):
        """mouse1 click"""

    def event_click2(self, event):
        """mouse2 click"""

    def event_esc(self, event):
        """escape key-abort work"""

    def deactivate(self):
        """stop and save work"""
