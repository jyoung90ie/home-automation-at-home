import socket
import struct
import textwrap
import sys

TAB = "\t"


def main():
    connection = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))

    while True:
        try:
            raw_data, addr = connection.recvfrom(65536)

            print(raw_data)

            dest_mac, src_mac, eth_proto, data = ethernet_frame(raw_data)
            print("\nEthernet Frame: ")
            print(
                "Destination: {}, Source: {}. Protocol: {}".format(
                    dest_mac, src_mac, eth_proto
                )
            )

            if eth_proto == 8:
                (version, header_length, ttl, proto, src, target, data) = ipv4_packet(
                    data
                )
                print(TAB + "IPv4 Packet:")
                print(
                    TAB * 2
                    + "Version: {}, Header Length: {}, TTL: {}".format(
                        version, header_length, ttl
                    )
                )
                print(
                    TAB * 2
                    + "Protocol: {}, Source: {}, Target: {}".format(proto, src, target)
                )

                if proto == 1:
                    icmp_type, src, target, data = icmp_packet(data)
                    print(TAB + "ICMP Packet:")
                    print(
                        TAB * 2
                        + "Type: {}, Code: {}, Checksum: {}".format(
                            icmp_type, src, target
                        )
                    )
                    print(TAB * 2 + "Data: {}".format(data))
                elif proto == 6:
                    (
                        src_port,
                        dest_port,
                        sequence,
                        acknowledgement,
                        flag_urg,
                        flag_ack,
                        flag_psh,
                        flag_rst,
                        flag_sync,
                        flag_fin,
                        data,
                    ) = tcp_segment(data)

                    print(TAB + "TCP Packet:")
                    print(
                        TAB * 2
                        + "Source Port: {}, Destination Port: {}".format(
                            src_port, dest_port
                        )
                    )
                    print(
                        TAB * 2
                        + "Sequence: {}, Acknowledgement: {}".format(
                            sequence, acknowledgement
                        )
                    )
                    print(TAB * 2 + "Flags: ")
                    print(
                        TAB * 3
                        + "URG: {}, ACK: {}, PSH: {}, RST: {}, SYN: {}, FIN: {}".format(
                            flag_urg, flag_ack, flag_psh, flag_rst, flag_sync, flag_fin
                        )
                    )
                    print(TAB * 3 + "Data: ")
                    print(format_multi_line(TAB * 3, data))

                elif proto == 17:
                    src_port, dest_port, target = udp_segment(data)
                    print(TAB + "UDP Packet:")
                    print(
                        TAB * 2
                        + "Source Port: {}, Destination Port: {}, Size: {}".format(
                            src_port, dest_port, target
                        )
                    )

        except socket.error as ex:
            print(ex)
            sys.exit()


# unpack ethernet frame
def ethernet_frame(data):
    dest_mac, src_mac, protocol = struct.unpack("! 6s 6s H", data[:14])

    return (
        get_mac_addr(dest_mac),
        get_mac_addr(src_mac),
        socket.htons(protocol),
        data[14:],
    )


def get_mac_addr(bytes_address):
    """Return formatted MAC address"""
    bytes_str = map("{:02x}".format, bytes_address)
    return ":".join(bytes_str).upper()


def ipv4_packet(data):
    """Unpacks IP4 packet"""
    version_header_length = data[0]
    version = version_header_length >> 4
    header_length = (version_header_length & 15) * 4
    ttl, protocol, src, target = struct.unpack("! 8x B B 2x 4s 4s", data[:20])

    return (
        version,
        header_length,
        ttl,
        protocol,
        ipv4(src),
        ipv4(target),
        data[header_length:],
    )


def ipv4(address):
    return ".".join(map(str, address))


def icmp_packet(data):
    """Unpacks ICMP packet"""
    icmp_type, code, checksum = struct.unpack("! B B H", data[:4])
    return icmp_type, code, checksum, data[4:]


def tcp_segment(data):
    (
        src_port,
        dest_post,
        sequence,
        acknowledgement,
        offset_reserved_flags,
    ) = struct.unpack("! H H L L H", data[:14])
    offset = (offset_reserved_flags >> 12) * 4
    flag_urg = (offset_reserved_flags & 32) >> 5
    flag_ack = (offset_reserved_flags & 16) >> 4
    flag_psh = (offset_reserved_flags & 8) >> 3
    flag_rst = (offset_reserved_flags & 4) >> 2
    flag_sync = (offset_reserved_flags & 2) >> 1
    flag_fin = offset_reserved_flags & 1

    return (
        src_port,
        dest_post,
        sequence,
        acknowledgement,
        flag_urg,
        flag_ack,
        flag_psh,
        flag_rst,
        flag_sync,
        flag_fin,
        data[offset:],
    )


def udp_segment(data):
    src_port, dest_port, size = struct.unpack("! H H 2x H", data[:8])
    return src_port, dest_port, size


def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string, bytes):
        string = "".join(r"\x{:02x}".format(byte) for byte in string)
        if size % 2:
            size -= 1
    return "\n".join([prefix + line for line in textwrap.wrap(string, size)])


main()
