ENTRY(_start)

SECTIONS
{   
    .nloader : {
        KEEP(*(.nloader))
    }

    .dtb : ALIGN(8) { 
        __dtb_start = ABSOLUTE(.);
        KEEP(*(.dtb)) 
        __dtb_end = .;
    }  
    
    .linux 0x80000 : { 
        __linux_start = .;
        KEEP(*(.linux)) 
        __linux_end = .;
    }  
    
    .initramfs : ALIGN(0x200000) { 
        __initramfs_start = ABSOLUTE(.);
        KEEP(*(.initramfs)) 
        __initramfs_end = .;
    }  
}
