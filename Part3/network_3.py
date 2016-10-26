'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize)
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    packet_id_length = 2
    fragflag_length = 1
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, packet_id, fragflag, data_S):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.packet_id = packet_id
        self.fragflag = fragflag
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        dest = str(self.dst_addr).zfill(self.dst_addr_S_length)
        packid = str(self.packet_id).zfill(self.packet_id_length)
        ff = str(self.fragflag).zfill(self.fragflag_length)
        byte_S = dest + packid + ff + self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        packet_id = int(byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.packet_id_length])
        fragflag = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.packet_id_length : NetworkPacket.dst_addr_S_length + NetworkPacket.packet_id_length + NetworkPacket.fragflag_length])
        data_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.packet_id_length + NetworkPacket.fragflag_length : ]
        return self(dst_addr, packet_id, fragflag, data_S)

    @classmethod
    def create_fragments(cls, dst_addr, data_S, mtu):
        extra = NetworkPacket.packet_id_length + NetworkPacket.dst_addr_S_length + NetworkPacket.fragflag_length
        maxdatasize = mtu - extra
        raw_packets = []
        # Check if packet is too big to send.
        if (len(data_S) > maxdatasize):
            data_frags = []
            location = 0
            i = 0
            # Create
            while (len(data_S) > location):
                if (location + maxdatasize >= len(data_S)):
                    # Location to the end
                    data_frags.append(data_S[location:])
                else:
                    # Location up to maxdatasize more stuff
                    data_frags.append(data_S[location: location + maxdatasize])
                location += maxdatasize
                i += 1
            i = 0
            for data_segment in data_frags:
                if (i == len(data_frags) - 1):
                    p = NetworkPacket(dst_addr, i, 0, data_segment)
                else:
                    p = NetworkPacket(dst_addr, i, 1, data_segment)
                i += 1
                raw_packets.append(p.to_byte_S())
        else:
            p = NetworkPacket(dst_addr, 0, 0, data_S)
            raw_packets.append(p.to_byte_S())  # send packets always enqueued successfully
        return raw_packets

## Implements a network host for receiving and transmitting data
class Host:
    packets_recieved = []
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        # Create a bunch of packets
        packets = NetworkPacket.create_fragments(dst_addr, data_S, 50)
        for packet in packets:
            self.out_intf_L[0].put(packet)
        
    # receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            p = NetworkPacket.from_byte_S(pkt_S)
            # Check if packet is part of a sequence
            if(p.fragflag == 0 and p.packet_id == 0):
                print('%s: received packet "%s"' % (self, pkt_S))
            else:
                print('%s: received fragment packet "%s"' % (self, pkt_S))
                #Packet fragments need to be reassembled.
                if(p.fragflag == 0):
                    #This is the last packet. Put everything together.
                    data = ''
                    for packet in self.packets_recieved:
                        data += packet.data_S
                    data += p.data_S
                    self.packets_recieved = []
                    print('%s: Reassembled packet "%s"' % (self, data))
                else:
                    self.packets_recieved.append(p)
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:

    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size, routing_table):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

        self.routing_table = routing_table
    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        mtu = 30 # Hard coded because bad programming habits. :(
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    if(len(pkt_S) > mtu):
                        #Need to get packet information.
                        p = NetworkPacket.from_byte_S(pkt_S)

                        packets = NetworkPacket.create_fragments(p.dst_addr, p.data_S, mtu)
                        for packet in packets:
                            self.out_intf_L[self.find_interface(i, NetworkPacket.from_byte_S(packet).dst_addr)].put(packet, True)
                        pass
                    else:
                        p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                        self.out_intf_L[self.find_interface(i, p.dst_addr)].put(p.to_byte_S(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, i))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass

    def find_interface(self, source, dest):
        for tuple in self.routing_table:
            if(tuple[0] == source and tuple[1] == dest):
                return tuple[2]
        print('Couldnt Find Route:')
        print(source)
        print(dest)
        return -1
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
           