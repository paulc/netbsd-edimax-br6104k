
NETBSDSRCDIR	 =	/usr/src
TOOLDIR			 =  /usr/src/tooldir.NetBSD-3.1-i386
DESTDIR			 =  /usr/src/obj/destdir.evbmips
CC				:=	$(TOOLDIR)/bin/mipsel--netbsd-gcc

CFLAGS			:= 	-O2 -Wall -nostdinc -isystem $(DESTDIR)/usr/include
LDFLAGS			:=	-Wl,-nostdlib -Wl,-dynamic-linker=/libexec/ld.elf_so \
					-Wl,-rpath-link,$(DESTDIR)/lib:$(DESTDIR)/usr/lib -Wl,-Bstatic \
					-B$(DESTDIR)/usr/lib/ -L$(DESTDIR)/lib -L$(DESTDIR)/usr/lib 

MAKEOBJDIR		 = ./obj
PROG			 = init

.include <bsd.prog.mk>
