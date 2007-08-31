#!/bin/sh

set -v

ROOT=$(pwd)/root
STRIP=${STRIP:-/usr/src/tooldir.NetBSD-3.1-i386/bin/mipsel--netbsd-strip}

rm -rf $ROOT
mkdir $ROOT
mtree -U -f mtree.edimax -p $ROOT
tar cpf - -C ${DESTDIR:-/usr/src/obj/destdir.evbmips} -T files | tar xvpf - -C $ROOT
cap_mkdb -l -v -f $ROOT/usr/share/misc/termcap termcap.min

cd $ROOT
    find bin sbin libexec usr/bin usr/sbin usr/libexec -type f -perm -100 | xargs ${STRIP}
    find lib usr/lib -type f | xargs ${STRIP}

cd $ROOT/dev
    ./MAKEDEV std md0 sd0

cd $ROOT/etc
    cat > fstab <<-EOM
		/dev/md0a / ffs rw,noatime
	EOM
    cat > gettytab <<-EOM
		default:\
		     ce:ck:np:im=\r\n%s/%m (%h) (%t)\r\n\r\n:sp#115200:
	EOM
    ex -s rc.conf <<-EOM
		/rc_configured/s/NO/YES/
		$
		a
		no_swap=YES
		.
		:wq
	EOM
    ex -s master.passwd <<-EOM
		/^root/s/csh/sh/
		:wq
	EOM
    pwd_mkdb -d .. -p -L master.passwd

cd $ROOT/etc/rc.d
    cat > DISKS <<-EOM
		# PROVIDE: disks
	EOM

cd $ROOT/root
    cat > .profile <<-EOM
		export PATH=/sbin:/usr/sbin:/bin:/usr/bin
		export ENV=$HOME/.shrc
	EOM
	cat > .shrc <<-EOM
		case "\$-" in *i*)
		    export EDITOR=vi
		    set -o emacs
		    set -o tabcomplete
			;;
		esac
	EOM

