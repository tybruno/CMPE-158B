import click

from socket import AF_INET, SOCK_DGRAM, socket
from struct import unpack
from threading import Thread


class TFTPServer:
    RRQ_OPCODE = 1

    def __init__(self, data_dir, tftp_port):
        self.data_dir = data_dir
        self.tftp_port = tftp_port

    def start(self):
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        # TODO we are binding on all addresses by using "", we probably want
        #      to be able to specify specific addresses we want to listen on.
        self.server_socket.bind(("", self.tftp_port))
        click.echo(
            "serving files from {} on port {}".format(self.data_dir, self.tftp_port)
        )
        self.tftp_thread = Thread(target=self.__process_requests, name="tftpd")
        self.tftp_thread.start()

    def __process_requests(self):
        print("waiting for request")
        # TODO is 1024 really the right size? should we make this a const?
        pkt, addr = self.server_socket.recvfrom(1024)
        # the first two bytes of all TFTP packets is the opcode, so we can
        # extract that here. need network-byte order hence the '!'.
        [opcode] = unpack("!H", pkt[0:2])
        if opcode == TFTPServer.RRQ_OPCODE:
            # RRQ is a series of strings, the first two being the filename
            # and mode but there may also be options. see RFC 2347.
            #
            # we skip the first 2 bytes (the opcode) and split on b'\0'
            # since the strings are null terminated.
            #
            # because b'\0' is at the end of all strings split will always
            # give us an extra empty string at the end, so skip it with [:-1]
            strings_in_RRQ = pkt[2:].split(b"\0")[:-1]
            print("got {} from {}".format(strings_in_RRQ, addr))
        else:
            print("cannot process {} from {}".format(opcode, pkt))

    def join(self):
        self.tftp_thread.join()


@click.command()
@click.option(
    "--data_dir",
    default=".",
    metavar="root_of_files_to_serve",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="the directory to use as the root of the files being served",
)
@click.option(
    "--tftp_port",
    default=69,
    metavar="UDP_listening_port",
    help="the UDP port to listen for tftp client requests",
)
def do_tftpd(data_dir, tftp_port):
    """ this is a simple TFTP server that will listen on the specified
        port and serve data rooted at the specified data. only read
        requests are supported for security reasons.
    """
    srvr = TFTPServer(data_dir, tftp_port)
    srvr.start()
    srvr.join()


if __name__ == "__main__":
    do_tftpd()
