import sys, copy
from ipaddress import ip_network

# Values for policy matching
ALLOW = 1
CONTINUE = 0
DROP = -1

# Values indicating inbound / outbound bgp policy
INBOUND = 10
OUTBOUND = 20

class Network:
    def __init__(self):
        self._devices = {}

    # build topology: device_name -> device
    def build_topo(self, data):
        for d in data['Devices']:
            device = Device(d['Name'], d)
            self._devices[d['Name']] = device

    # broadcast the topology to all devices so that action "sending" 
    # can be done by calling the next switch's "receive_bgp_ad" function
    def broadcast_topo(self):
        for d in self._devices:
            self._devices[d].set_topo(self._devices)

    # begin bgp process
    def begin_bgp(self):
        for d in self._devices:
            self._devices[d].construct_ads()
        # After broadcast done, construct forwarding tables
        print("\nGenerating forwarding tables...")
        print("-------------------------------")
        for d in self._devices:
            self._devices[d].construct_forwarding_table()
        print("\n")

    def check_forwarding_tables(self, check_table):
        for switch in check_table:
            generated_table = self._devices[switch].get_forwarding_table()
            supposed_table = check_table[switch]
            for prefix in supposed_table:
                supposed_list = supposed_table[prefix]
                if prefix not in generated_table:
                    return False
                generated_list = generated_table[prefix]
                for interface in supposed_list:
                    if interface not in generated_list:
                        return False
                    generated_list.remove(interface)
                if len(generated_list) != 0:
                    return False
        return True
                

class Device:
    def __init__(self, name, device):
        self._name = name
        
        self._interfaces = {}
        for i in device['Interfaces']:
            self._interfaces[i['Name']] = i

        self._ads = device['BgpConfig'][0]['AdvertisedRoutes']

        self._config = {}
        for policy in device['BgpConfig'][1]['InboundPolicies']:
            self._config[policy['Name']] = policy
        for policy in device['BgpConfig'][2]['OutboundPolicies']:
            self._config[policy['Name']] = policy

        self._static_routes = device['StaticRoutes']

        # We don't need to care about Acls
        # self._acl = device['Acls']

        self._network = {}
        self._bgp_prefs = {}
        self._forwarding_table = {}


    def set_topo(self, network):
        self._network = network


    # construct and broadcast bgp advertisements, with no last_interface
    def construct_ads(self):
        ads_list = []
        for prefix in self._ads:
            ads_list.append(AdMessage(prefix))
        for ad in ads_list:
            self.broadcast_ad(ad, '')


    # variable: last = from which interface does this device receive this advertisement
    def broadcast_ad(self, ad, last):
        ad.add_hop(self._name)
        for i in self._interfaces:
            interface = self._interfaces[i]
            next_interface = interface['Neighbor']
            policy_name = interface['OutBgpPolicy']
            if next_interface and i != last:
                if policy_name:
                    # We need deepcopy of the advertisement for boardcasting multiple
                    # copies of current advertisements to multiple interfaces
                    new_ad, allow = self.match_policy(copy.deepcopy(ad), self._config[policy_name], OUTBOUND, last)
                else:
                    new_ad, allow = copy.deepcopy(ad), True
                    print("No Policy, default allowed")
                if allow:
                    next_hop = next_interface.split('@', 1)[0]
                    print(self._name + " send prefix: " + new_ad.get_prefix() + " to " + next_hop + "\n")
                    self._network[next_hop].receive_bgp_ad(next_interface, new_ad)


    # variable: last = from which interface does this device receive this advertisement
    def receive_bgp_ad(self, last, ad):
        # Advertisement loop checking
        if ad.check_hop(self._name):
            print("Advertisement dropped!\n")
            return
        
        policy_name = self._interfaces[last]['InBgpPolicy']
        if policy_name:
            # We don't need deep copy of ad here because it will be only dealt once
            new_ad, allow = self.match_policy(ad, self._config[policy_name], INBOUND, last)
        else:
            new_ad, allow = ad, True
            print("No Policy, default allowed")
            # update bgp_prefs if we defaultly accept this advertisement
            if ad.get_prefix() not in self._bgp_prefs:
                self._bgp_prefs[ad.get_prefix()] = bgp_pref(ad.get_prefix(), 100, last)
            else:
                allow = self._bgp_prefs[ad.get_prefix()].set_hop(100, last)         
        if allow:
            print(self._name + " received prefix: " + new_ad.get_prefix() + " from interface " + last + "\n")
            self.broadcast_ad(new_ad, last)


    def match_policy(self, ad, policy, bound, last):
        print("Matching Policy: " + policy['Name'])
        for p in policy['PolicyClauses']:
            matches = p['Matches']

            # Matching the last entry []
            if not matches:
                allow = self.do_action(ad, p['Actions'], bound, last)
                return ad, allow == ALLOW

            for single_policy in p['Matches']:
                print("Matching Policy: " + single_policy)
                p_type, p_value = single_policy.split(": ", 1)
                if (p_type == "prefix" and ad.check_prefix(p_value)) or \
                (p_type == "tag" and ad.check_tag(p_value)) or \
                (p_type == "neighbor" and ad.get_last_hop() == p_value): 
                    allow = self.do_action(ad, p['Actions'], bound, last)
                    if allow != CONTINUE:
                        return ad, allow == ALLOW
                    # allow == CONTINUE then continue
                
                if p_type != "prefix" and p_type != "tag" and p_type != "neighbor":
                    print("Error: Unknown Match")
                    sys.exit()

            
    def do_action(self, ad, actions, bound, last):
        if bound == INBOUND:
            if ad.get_prefix() in self._bgp_prefs:
                pref = copy.deepcopy(self._bgp_prefs[ad.get_prefix()])
                if not pref.set_hop(100, last):
                    return ad, False
            else:
                pref = bgp_pref(ad.get_prefix(), 100, last)

        for a in actions:
            print("Apply action: " + a)
            if a == 'allow':
                if bound == INBOUND:
                    self._bgp_prefs[ad.get_prefix()] = pref
                return ALLOW
            elif a == 'drop':
                print("\n")
                return DROP
            else:
                a_list = a.split(' ')
                if a_list[1] == 'tag':
                    if a_list[0] == 'add':
                        ad.add_tag(a_list[2])
                    elif a_list[0] == 'remove':
                        ad.remove_tag(a_list[2])
                    else:
                        print("Error: Unknown Tag Action")
                        sys.exit()
                elif a_list[0] == 'set' and a_list[1] == 'localpref':
                    if not pref.set_hop(int(a_list[2]), last):
                        return ad, False
                
        return CONTINUE

    
    def construct_forwarding_table(self):
        for s_route in self._static_routes:
            self._forwarding_table[s_route['Prefix']] = [s_route['Interface']]
        for bgp_pref in self._bgp_prefs:
            # Avoid conflict with static routes
            if bgp_pref not in self._forwarding_table:
                self._forwarding_table[bgp_pref] = copy.deepcopy(self._bgp_prefs[bgp_pref]._hop_name)
        print("Forwarding table of " + self._name)
        print(self._forwarding_table)


    def get_forwarding_table(self):
        return self._forwarding_table


class AdMessage:
    def __init__(self, prefix):
        self._prefix = prefix
        self._path = []
        self._tag = []

    def get_prefix(self):
        return self._prefix

    def add_hop(self, switch):
        self._path.append(switch)

    def get_last_hop(self):
        return self._path[-1]

    def check_hop(self, switch):
        return switch in self._path
    
    def check_prefix(self, target):
        local_list = self._prefix.split('/')
        target_list = target.split('/')
        target_length = target_list[-1].replace('[', '').replace(']', '').split('-')

        if int(local_list[-1]) <= int(target_length[1]) and int(local_list[-1]) >= int(target_length[0]):
            local_network = ip_network(self._prefix.decode('utf-8'))
            target_network = ip_network((target_list[0] + '/' + target_length[0]).decode('utf-8'))
            return local_network.subnet_of(target_network)
        return False

    def add_tag(self, tag):
        if tag in self._tag:
            print("Error: Tag already exist!")
            # sys.exit()
        else:
            self._tag.append(tag)
    
    def check_tag(self, tag):
        return tag in self._tag
    
    def remove_tag(self, tag):
        if tag not in self._tag:
            print("Error: Tag doesn't exist!")
            # sys.exit()
        else:
            self._tag.remove(tag)


class bgp_pref:
    def __init__(self, prefix, pref, hop_name):
        self._prefix = prefix
        self._pref = pref
        self._hop_name = [hop_name]
    
    def set_hop(self, pref, hop_name):
        if pref > self._pref:
            self._pref = pref
            self._hop_name = [hop_name]
            return True
        elif pref == self._pref:
            if hop_name not in self._hop_name:
                self._hop_name.append(hop_name)
            return True
        # don't update if given pref is smaller
        print("Preference Issue")
        return False