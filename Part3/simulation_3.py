'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import threading
from time import sleep

import link_3

import network_3

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 5 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network nodes
    tablet = network_3.Host(1)
    object_L.append(tablet)
    client = network_3.Host(2)
    object_L.append(client)
    server = network_3.Host(3)
    object_L.append(server)

    #Router Configurations!
    table_a = [(0, 3, 0), (1, 3, 1)] # From Host 1 to Host 3, send to router B, From Host 2 to 3 send to C.
    table_b = [(0, 3, 0)]  # Recieve on interface 0 for 3 send 0
    table_c = [(1, 3, 0)]
    table_d = [(0, 3, 0), (1, 3, 0)] # Send everything to port 0.


    router_a = network_3.Router(name='A', intf_count=2, max_queue_size=router_queue_size, routing_table=table_a)
    object_L.append(router_a)
    router_b = network_3.Router(name='B', intf_count=2, max_queue_size=router_queue_size, routing_table=table_b)
    object_L.append(router_b)
    router_c = network_3.Router(name='C', intf_count=2, max_queue_size=router_queue_size, routing_table=table_c)
    object_L.append(router_c)
    router_d = network_3.Router(name='D', intf_count=2, max_queue_size=router_queue_size, routing_table=table_d)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_3.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    link_layer.add_link(link_3.Link(tablet, 0, router_a, 0, 50))
    link_layer.add_link(link_3.Link(client, 0, router_a, 1, 50))
    link_layer.add_link(link_3.Link(router_a, 0, router_b, 0, 50))
    link_layer.add_link(link_3.Link(router_a, 1, router_c, 1, 50))
    link_layer.add_link(link_3.Link(router_b, 0, router_d, 0, 50))
    link_layer.add_link(link_3.Link(router_c, 0, router_d, 1, 50))
    link_layer.add_link(link_3.Link(router_d, 0, server, 0, 50))
    
    
    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client.__str__(), target=client.run))
    thread_L.append(threading.Thread(name=tablet.__str__(), target=tablet.run))
    thread_L.append(threading.Thread(name=server.__str__(), target=server.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))
    
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events    
    for i in range(1):
        client.udt_send(3, 'Im a laptop!')
        tablet.udt_send(3, 'Im a tablet!')

    
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically