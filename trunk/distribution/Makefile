
CC		= /usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-gcc
LD		= /usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-ld
NM		= /usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-nm
STRIP	= /usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-strip
OBJCOPY	= /usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-objcopy
CONF	?= ADM5120-EDIMAX-MFS
MDSIZE  ?= 8000b
ROOTDIR ?= root
WORKDIR := $(CONF)
KERNEL	:= /usr/src/sys/arch/evbmips/compile/obj/$(CONF)/netbsd
MFSROOT != ( $(NM) $(KERNEL) | grep -c md_root_image ) || true
DESTDIR	= /usr/src/obj/destdir.evbmips
COPYDEST = paulc@172.16.246.1:Development/Edimax/Work

.if $(MFSROOT) == 1
all : mdimage copy
.else
all : image copy
.endif

copy : $(WORKDIR)/netbsd.bin.gz
	scp $(WORKDIR)/netbsd.bin.gz $(COPYDEST)/netbsd-$(CONF)

image : $(WORKDIR)/netbsd
	$(OBJCOPY) -O binary $(WORKDIR)/netbsd $(WORKDIR)/netbsd.bin
	gzip -9 -c $(WORKDIR)/netbsd.bin > $(WORKDIR)/netbsd.bin.gz

mdimage : $(WORKDIR)/netbsd $(WORKDIR)/root.img
	mdsetimage -sv $(WORKDIR)/netbsd $(WORKDIR)/root.img
	$(OBJCOPY) -O binary $(WORKDIR)/netbsd $(WORKDIR)/netbsd.bin
	gzip -9 -c $(WORKDIR)/netbsd.bin > $(WORKDIR)/netbsd.bin.gz

$(WORKDIR)/netbsd : $(KERNEL) $(WORKDIR)
	cp $(KERNEL) $(WORKDIR)/netbsd

$(WORKDIR)/root.img : .rootfs
	su root -c "makefs -s $(MDSIZE) -o minfree=0,bsize=4096,fsize=512,density=16000 $(WORKDIR)/root.img $(ROOTDIR)"

workdir : $(WORKDIR)

$(WORKDIR) :
	mkdir $(WORKDIR)

rootfs: .rootfs

.rootfs: mtree.edimax files
	DESTDIR=$(DESTDIR) STRIP=$(STRIP) su root mkrootfs.sh
	touch .rootfs

clean:
	rm -rf $(WORKDIR) *~

cleanrootfs:
	su root -c "rm -rf root .rootfs"
