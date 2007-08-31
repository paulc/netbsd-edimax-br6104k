/* Simple linker script with just a text section. 
  text == program code.
*/

SECTIONS {
	. = 0x80500000;       /* loader loads us here */
	_code_start = .;      
	.text : {
		*(.text)
	}
	_code_end = .;
	.data : {
		*(.data)
	}
}
