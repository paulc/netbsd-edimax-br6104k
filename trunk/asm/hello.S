
#include <mips/regdef.h>

	.org	0x6d8              // Origin offset required by Edimax bootloader

	.set noreorder
	
	la	t0, __linked_address    // t0 contains linked address.	
	bal	__linked_address		
	nop
__linked_address:
					// ra now contains actual address.
	subu	t0, ra, t0		// Difference between linked and actual
	la	t1, _code_start		// load linked address
	la	t2, _code_end		//   "    "       "
	addu	t0, t0, t1		// t0 now has current address


__copy:
	lw	t3, 0(t0)               // Copy *t0 -> *t1 until t2 
	sw	t3, 0(t1)               // 
	addu	t1, 4
	blt	t1, t2, __copy	
	addu	t0, 4
	
	.set reorder

	la      t1,__hello_world
        la      t0,0xb2600018        # Serial port status address
__start:
        lw      v0,0(t0)             # load the register value v0 = *(t0)
        andi    v0,v0,0x80           # check to see if ready to send
        beqz    v0,__start           # if unset, go round the loop again
        nop                          # if set, wait one clock cycle before writing
        la      v1,0xb2600000        # serial port fifo.
        lb      v0,0(t1)             # load the character to write
        sw      v0,0(v1)             # store the word
	addu    t1,t1,1
	beqz    v0, __finish         # Bail out on null terminator
	nop
	b       __start
	nop

__finish:
	b      __finish
	wait			# suspend the CPU
__hello_world:
	.ascii  "Hello World!\0"

