include ../x7-lib/common.mk

help-more:
	@echo "icons - build all icons, if needed"
	@echo "icons_test - build just a couple of icons for testing"

.PHONY: icons icons_test

INKSCAPE := /Applications/Inkscape.app/Contents/MacOS/inkscape
ICONS_SRC := x7/view/resources/icons-src
ICONS_GEN := x7/view/resources/icons
icon_names := $(patsubst $(ICONS_SRC)/%.svg,%,$(wildcard $(ICONS_SRC)/*.svg))
icon_sizes := 16 24 32 64
icons_all := $(foreach size,$(icon_sizes),$(foreach name,$(icon_names),$(ICONS_GEN)/$(name)-$(size)x$(size).png))
define ICON_template
$$(ICONS_GEN)/%-$(1)x$(1).png: $$(ICONS_SRC)/%.svg
	$$(INKSCAPE) -o $$@ -w $(1) -h $(1) $$<
endef
$(foreach size,$(icon_sizes),$(eval $(call ICON_template,$(size))))

icons_test: $(ICONS_GEN)/redo-32x32.png $(ICONS_GEN)/undo-24x24.png

icons: $(icons_all)
