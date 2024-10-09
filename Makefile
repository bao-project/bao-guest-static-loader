
ifeq ($(and $(IMAGE), $(DTB), $(TARGET), $(ARCH)),)
ifneq ($(MAKECMDGOALS), clean)
 $(error Linux image (IMAGE) and/or device tree (DTB) and/or target name \
 	(TARGET) and/or architecture (ARCH) not specified)
endif
endif

ARCH=aarch64
ifeq ($(ARCH), aarch64)
CROSS_COMPILE?=aarch64-none-elf-
OPTIONS=-mcmodel=large 
else ifeq ($(ARCH), aarch32)
CROSS_COMPILE?=arm-none-eabi-
OPTIONS=-march=armv7-a
else ifeq ($(ARCH), riscv)
CROSS_COMPILE?=riscv64-unknown-elf-
OPTIONS=-mcmodel=medany
else
$(error unkown architecture $(ARCH))
endif

MODIFIED_DTB=modified.dtb

INITRD_OFFSETS +=

ifeq ($(INITRAMFS),)
TARGET_DTB=$(DTB)
else
TARGET_DTB=$(MODIFIED_DTB)
endif

all: $(TARGET).bin

clean:
	-rm *.elf *.bin $(MODIFIED_DTB)

.PHONY: all clean
	
$(TARGET).bin: $(TARGET).elf
	$(CROSS_COMPILE)objcopy -S -O binary $(TARGET).elf $(TARGET).bin

$(TARGET).elf: $(ARCH).S $(IMAGE) loader_$(ARCH).ld $(TARGET_DTB) $(if $(INITRAMFS), $(INITRAMFS))
	$(CROSS_COMPILE)gcc -Wl,-build-id=none -nostdlib -T loader_$(ARCH).ld \
		-o $(TARGET).elf $(OPTIONS) $(ARCH).S -I. -D IMAGE=$(IMAGE) -D DTB=$(TARGET_DTB) \
		$(if $(INITRAMFS),-D INITRAMFS=$(INITRAMFS) $(INITRD_OFFSETS))

$(MODIFIED_DTB):
INITRD_OFFSETS += $(shell python3 dtb_initrd_modifier.py $(DTB) root=/dev/ram0 $(MODIFIED_DTB))

