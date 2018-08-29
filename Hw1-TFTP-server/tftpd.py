import click

from socket import AF_INET, SOCK_DGRAM, socket
from struct import unpack, pack
from threading import Thread


class TFTPServer:
    RRQ_OPCODE = 1
    DATAPKT_OPCODE = 3
    ACK_OPCODE = 4
    ERROR_OPCODE = 5

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

       
        self.tftp_thread = Thread(target=self.__start_tftp, name="tftpd")
        self.tftp_thread.start()
        
    def __start_tftp(self):
        """
        This section starts the tftp connection. It also sends and receives data.
        """
        (opcode, hostname,port, f) = self.__process_requests()

        if opcode is TFTPServer.RRQ_OPCODE:
            data = self.__get_data(f)
            self.__send_data(data,hostname,port)
            

        
    def __send_data(self,data,hostname,port):
        """
        Sends data to the specified client

        Args:
            data (str): data that will be sent to the client
            hostname (str): The client's hostname 
            port (str): port used to communicate with client
        """
        block_number = 1
        size = len(data)
        for section in data:
          
            packet_template = pack('!HH',3,block_number)
            data_packet = packet_template + section
         
            print(f"data_packet sent: {data_packet}")
            
            self.server_socket.sendto(data_packet,(hostname,port))
    
            if size is not block_number:    
                output = self.__process_requests()
                if output is block_number:
                    print(f"Client received block {block_number}")
                
            block_number += 1
               
            

        print("Data sent")
          
    def __get_data(self,f):
        """
        Gets data from a file on the host server and returns the data

        Args:
            f (str): is the file that will be read

        Returns:
            data (list): list filled with the data from the lines in the file
        """
        READ_SIZE = 512
        DELAY = 30

        output = []

        count = 0
        
    
        # I used the following to help guide me https://stackoverflow.com/questions/6787233/python-how-to-read-bytes-from-file-and-save-it
        with open(f,"rb") as file:
          
            while True:
                
                section = file.read(READ_SIZE)
                
                if section.decode('utf-8') is "" or count is DELAY:
             
                    output.append(section)
                    return output
                output.append(section)
                count+=1
           

    def __process_requests(self):
        """
        Process a request from a tftp server
        Will handle read requests, acks, and errors
        """
        print("waiting for request")
        # TODO is 1024 really the right size? should we make this a const?
        pkt, addr = self.server_socket.recvfrom(1024)
        # print("here")
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
            f,mode = strings_in_RRQ

            f = f.decode('utf-8')
            hostname,port = addr
           
            print("got {} from {}".format(strings_in_RRQ, addr))

             
            return opcode,hostname,port,f
        elif opcode is TFTPServer.ACK_OPCODE:
            
            [block_number] = unpack("!H", pkt[2:4])
            

            return block_number
        elif opcode is TFTPServer.ERROR_OPCODE:

            strings_in_RRQ = pkt[2:].split(b"\0")[:-1]
            garbage, error_mssg = strings_in_RRQ
            error_mssg = error_mssg.decode('utf-8')
            print(error_mssg)
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
    help="the UDP  port to listen for tftp client requests",
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
    
        while True:
            try:
                do_tftpd()
            except KeyboardInterrupt:
                sys.exit()
