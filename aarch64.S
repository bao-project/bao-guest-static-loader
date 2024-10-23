#define STRINGIFY2(X) #X
#define STRINGIFY(X) STRINGIFY2(X)

.section .nloader, "a"
.global _start
_start:
    /* make sure all exceptions disabled */
    msr daifset, 0xf

    /* make sure mmu disable */
    mrs	x0, sctlr_el1
    mov x1, #1
    bic	x0, x0, x1
    msr	sctlr_el1, x0

    isb

    /* boot protocol */
    adr x0, __dtb_start
    mov x1, xzr
    mov x2, xzr
    mov x3, xzr
    
#ifdef INITRAMFS
    /* linux,initrd-start */
    adr x4, _start  //absolute address of this image .bin
    ldr x5, =__dtb_start
    add x5, x5, x4  //absolute adr of dtb

    ldr x6, =INITRD_START_OFFSET
    add x6, x5, x6 //absolute adr of linux,initrd-start property

    ldr x7, =__initramfs_start
    add x7, x7, x4 //absolute adr of initramfs
    rev w7, w7  //change to big endian

    str w7, [x6]

    /* linux,initrd-end */
    ldr x6, =INITRD_END_OFFSET
    add x6, x5, x6 //absolute adr of linux,initrd-end property

    ldr x7, =__initramfs_end
    add x7, x7, x4 //absolute adr of initramfs end
    rev w7, w7  //change to big endian

    str w7, [x6]

#endif //INITRAMFS

    /* jump to linux */
    ldr x4, =_start
    ldr x5, =__linux_start
    sub x4, x5, x4
    adr x5, _start
    add x5, x5, x4
    br x5

.section .linux, "a"
    .incbin STRINGIFY(IMAGE)

.section .dtb, "a"
    .incbin STRINGIFY(DTB)
 
#ifdef INITRAMFS
.section .initramfs, "a"
    .incbin STRINGIFY(INITRAMFS)
#endif //INITRAMFS
