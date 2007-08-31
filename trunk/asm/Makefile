#
# 'Hello world' Makefile for BR-6104KP experiments.

CROSS_COMPILE=/usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-

CC			:= $(CROSS_COMPILE)gcc
LD			:= $(CROSS_COMPILE)ld
OBJCOPY		:= $(CROSS_COMPILE)objcopy
OBJDUMP		:= $(CROSS_COMPILE)objdump

CFLAGS		=  -Wall -Wstrict-prototypes -Wno-trigraphs  \
		  -fno-strict-aliasing -fno-common -fomit-frame-pointer -G 0 \
		  -mno-abicalls -fno-pic -ffunction-sections -pipe -mlong-calls \
		  -fno-common -mabi=32 -march=mips32 -Wa,-32 -Wa,-march=mips32 \
		  -Wa,-mips32 -Wa,--trap -I/usr/src/obj/destdir.evbmips/usr/include

LDFLAGS		= -static -no-warn-mismatch

all: hello.bin.gz

%.o : %.S
	$(CC) -D__ASSEMBLY__ $(CFLAGS) -g0 -c -o $@ $<

upload: hello.bin.gz
	adm_tx -i $<

hello.bin.gz: hello.bin
	gzip -c $< > $@

hello.bin: hello.elf
	$(OBJCOPY) -O binary $< $@

hello.elf: hello.o hello.lds
	$(LD) $(LDFLAGS) -o $@ hello.o -T hello.lds

clean:
	rm -f *.gz *.elf *.bin *.o *~

dis:
	$(OBJDUMP)  -D hello.elf  | less
