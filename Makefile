ROMNAME=terminal64
SOURCE_DIR=src
BUILD_DIR=build
include $(N64_INST)/include/n64.mk

src = main.c \
      comm.c \
      game.c \
      graphics.c \
      util.c \

assets_png = $(wildcard assets/*.png)
assets_conv = $(addprefix filesystem/,$(notdir $(assets_png:%.png=%.sprite)))

MKSPRITE_FLAGS ?=

all: $(ROMNAME).z64

filesystem:
	@mkdir -p $@

filesystem/%.sprite: assets/%.png | filesystem
	@echo "    [SPRITE] $@"
	@$(N64_MKSPRITE) $(MKSPRITE_FLAGS) -o filesystem "$<"

filesystem/n64brew.sprite: MKSPRITE_FLAGS=--format RGBA16 --compress 0 --tiles 64,96
filesystem/tiles.sprite: MKSPRITE_FLAGS=--format RGBA16 --compress 0 --tiles 32,32

$(BUILD_DIR)/$(ROMNAME).dfs: $(assets_conv)
$(BUILD_DIR)/$(ROMNAME).elf: $(src:%.c=$(BUILD_DIR)/%.o)

$(ROMNAME).z64: N64_ROM_TITLE="Ballgames"
$(ROMNAME).z64: $(BUILD_DIR)/$(ROMNAME).dfs

clean:
	rm -rf build filesystem *.z64

deploy: $(ROMNAME).z64
	@sc64deployer upload $<

-include $(wildcard $(BUILD_DIR)/*.d)

.PHONY: all clean deploy

