V=1
SOURCE_DIR=src
BUILD_DIR=build
NAME=ballgames
include ./libdragon/n64.mk

all: $(NAME).z64
.PHONY: all

OBJS = $(BUILD_DIR)/main.o \
       $(BUILD_DIR)/comm.o \
	   $(BUILD_DIR)/game.o \
	   $(BUILD_DIR)/graphics.o \

hello.z64: N64_ROM_TITLE="Ballgames"

$(BUILD_DIR)/$(NAME).elf: $(OBJS)

clean:
	rm -f $(BUILD_DIR)/* *.z64
.PHONY: clean

deploy: $(NAME).z64
	@sc64deployer upload $<
.PHONY: deploy

-include $(wildcard $(BUILD_DIR)/*.d)