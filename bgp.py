import copy

class Network:
    def __init__(self):
        self._devices = {}

    def build_topo(self, data):
        for d in data['Devices']:
            device = Device(d['Name'], d)
            self._devices[d['Name']] = device

    def broadcast_topo(self):
        for d in self._devices:
            self._devices[d].set_topo(self._devices)

    def begin_bgp(self):
        for d in self._devices:
            self._devices[d].construct_ads()


class Device:
    def __init__(self, name, device):
        self._name = name
        
        self._interfaces = {}
        for i in device['Interfaces']:
            self._interfaces[i['Name']] = i

        self._ads = device['BgpConfig'][0]['AdvertisedRoutes']

        self._in_config = {}
        for policy in device['BgpConfig'][1]['InboundPolicies']:
            self._in_config[policy['Name']] = policy

        self._out_config = {}
        for policy in device['BgpConfig'][2]['OutboundPolicies']:
            self._out_config[policy['Name']] = policy

        self._static_routes = device['StaticRoutes']
        self._acl = device['Acls']

        self._network = {}
        self._bgp_prefs = []


    def set_topo(self, network):
        self._network = network

    def construct_ads(self):
        ads_list = []
        for prefix in self._ads:
            ads_list.append(AdMessage(prefix))
        
        for ad in ads_list:
            self.broadcast_ad(ad, '')
        
    def broadcast_ad(self, ad, last):
        ad.add_hop(self._name)
        for i in self._interfaces:
            interface = self._interfaces[i]
            next_interface = interface['Neighbor']
            if next_interface and i != last:
                next_hop = next_interface.split('@', 1)[0]
                print(self._name + " send prefix: " + ad.get_prefix() + " to " + next_hop)
                self._network[next_hop].receive_bgp_ad(next_interface, copy.deepcopy(ad))

    def receive_bgp_ad(self, in_interface, ad):
        if ad.check_hop(self._name):
            print("Message dropped!\n")
            return
        print(self._name + " received prefix: " + ad.get_prefix() + " from interface " + in_interface)
        print("do something")
        self.broadcast_ad(ad, in_interface)


    def get_device_name(self):
        return self._name

    



class AdMessage:
    def __init__(self, prefix):
        self._prefix = prefix
        self._path = []
        self._tag = []

    def get_prefix(self):
        return self._prefix

    def add_hop(self, switch):
        self._path.append(switch)

    def get_next_hop(self):
        return self._path[-1]

    def check_hop(self, switch):
        return switch in self._path
    
    def check_tag(self, tag):
        if tag in self._tag:
            return True
        else:
            return False
    
    def remove_tag(self, tag):
        self._tag.remove(tag)



class bgp_pref:
    def __init__(self, prefix, pref, hop_name):
        self._prefix = prefix
        self._pref = pref
        self._hop_name = [hop_name]
    