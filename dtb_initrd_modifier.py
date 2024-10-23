import sys
import struct
import fdt  

# Constants for FDT Magic number and tags
FDT_MAGIC = 0xd00dfeed
FDT_BEGIN_NODE = 0x1
FDT_END_NODE = 0x2
FDT_PROP = 0x3
FDT_NOP = 0x4
FDT_END = 0x9

def read_u32(data, offset):
    return struct.unpack_from(">I", data, offset)[0]

def parse_header(data):
    """Parses the DTB header and returns important offsets."""
    magic = read_u32(data, 0)
    if magic != FDT_MAGIC:
        raise ValueError("Invalid DTB file")

    totalsize = read_u32(data, 4)
    off_dt_struct = read_u32(data, 8)
    off_dt_strings = read_u32(data, 12)
    off_mem_rsvmap = read_u32(data, 16)

    return off_dt_struct, off_dt_strings

def align_to_4(offset):
    """Aligns the offset to the next 4-byte boundary."""
    return (offset + 3) & ~3

def parse_structure_block(data, struct_offset, strings_offset):
    """Parses the structure block to find specified properties."""
    offset = struct_offset
    linux_initrd_start_offset = None
    linux_initrd_end_offset = None

    while True:
        token = read_u32(data, offset)

        if token == FDT_BEGIN_NODE:
            # Read node name (null-terminated string)
            node_name_end = data.find(b'\x00', offset + 4)
            node_name = data[offset + 4:node_name_end].decode()

            # Move offset past the node name (including null byte)
            offset = node_name_end + 1
            # Align to 4 bytes after node name
            offset = align_to_4(offset)

        elif token == FDT_END_NODE:
            offset += 4  # Move past FDT_END_NODE

        elif token == FDT_PROP:
            # Property format: [length, name offset, value]
            prop_len = read_u32(data, offset + 4)
            name_offset = read_u32(data, offset + 8)
            prop_value_offset = offset + 12

            # Get the property name from the strings block
            prop_name_end = data.find(b'\x00', strings_offset + name_offset)
            prop_name = data[strings_offset + name_offset:prop_name_end].decode()

            # Check for specific properties and store their offsets
            if prop_name == "linux,initrd-start":
                linux_initrd_start_offset = prop_value_offset
            elif prop_name == "linux,initrd-end":
                linux_initrd_end_offset = prop_value_offset

            # Move offset past property (align to 4 bytes)
            offset = align_to_4(prop_value_offset + prop_len)

        elif token == FDT_NOP:
            offset += 4  # Just skip NOP

        elif token == FDT_END:
            break  # End of structure block

        else:
            print(f"Unknown token {hex(token)} at offset {hex(offset)}")
            break

    return linux_initrd_start_offset, linux_initrd_end_offset

def modify_dtb(dtb_file, bootargs_addition, output_file):
    """Modifies the DTB file by adding the bootargs string and initrd properties."""
    # Load the DTB
    with open(dtb_file, 'rb') as f:
        dtb_data = f.read()

    dtb = fdt.parse_dtb(dtb_data)

    #chosen = dtb.get_node("chosen")

    if dtb.exist_node("chosen"):
        #print(chosen.name)
        bootargs = chosen.get_property("bootargs")

        if bootargs is not None:
            bootargs_data = bootargs.value + ' ' + bootargs_addition
            dtb.set_property('bootargs', bootargs_data, "/chosen")
        else:
            dtb.set_property('bootargs', bootargs_addition, "/chosen", True)
        
        dtb.set_property('linux,initrd-start', 0, "/chosen", True)
        dtb.set_property('linux,initrd-end', 0, "/chosen", True)
    else:
        chosen = fdt.Node('chosen')
        chosen.append(fdt.PropStrings('bootargs', bootargs_addition))
        chosen.append(fdt.PropWords('linux,initrd-start', 0))
        chosen.append(fdt.PropWords('linux,initrd-end', 0))
        dtb.add_item(chosen)

    node = dtb.get_node("chosen")
    for prop in node.props:
        print(prop.name)
        print(prop.value)

    with open(output_file, "wb") as f:
      f.write(dtb.to_dtb(version=17))



def main(dtb_file, bootargs_addition, output_file):

    # Modify the DTB with bootargs and initrd properties
    modify_dtb(dtb_file, bootargs_addition, output_file)

    with open(output_file, 'rb') as f:
        data = f.read()

    # Parse DTB header
    struct_offset, strings_offset = parse_header(data)

    # Parse structure block and find specified properties
    initrd_start_offset, initrd_end_offset = parse_structure_block(data, struct_offset, strings_offset)

    # Output offsets for use in Makefile as C flags
    if initrd_start_offset is not None:
        print(f"-D INITRD_START_OFFSET={hex(initrd_start_offset)}")
    if initrd_end_offset is not None:
        print(f"-D INITRD_END_OFFSET={hex(initrd_end_offset)}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 offsets.py <path_to_dtb_file> <bootargs_addition> <path_to_modified_dtb>")
    else:
        dtb_file = sys.argv[1]
        bootargs_addition = sys.argv[2]
        output_file = sys.argv[3]
        main(dtb_file, bootargs_addition, output_file)