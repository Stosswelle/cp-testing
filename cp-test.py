import sys, getopt
import yaml

import bgp


def main(argv):
    topo_file = ''
    query_file = ''

    # parse args
    try:
        opts, args = getopt.getopt(argv, "ht:q:")
    except getopt.GetoptError:
        print("dp-verify.py -t <topo file> -q <query file>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print("dp-verify.py -t <topo file> -q <query file>")
            sys.exit()
        elif opt == '-t':
            topo_file = arg
        elif opt == '-q':
            query_file = arg
    
    if topo_file == '' or query_file == '':
        print("dp-verify.py -t <topo file> -q <query file>")
        sys.exit()
    

    # build the network topology
    try:
        with open(topo_file, 'r') as f:
            data = yaml.safe_load(f)
    except IOError:
        print(topo_file + " doesn't existed!")
        sys.exit()
    
    network = bgp.Network()
    network.build_topo(data)
    network.broadcast_topo()
    network.begin_bgp()


    # build the query plan
    try:
        with open(query_file, 'r') as f:
            data = yaml.safe_load(f)
    except IOError:
        print(query_file + " doesn't existed!")
        sys.exit()

    rules = data['RoutingRules']
    for cases in rules:
        check_table = {}
        case = cases['Case']
        for rule in case:
            name = rule['Device']
            if name in check_table:
                t = check_table[name]
            else:
                t = {}
                check_table[name] = t
            t[rule['Prefix']] = rule['Interfaces']
        if network.check_forwarding_tables(check_table):
            print("**************************************")
            print("* Success! Control Plane is correct! *")
            print("**************************************")
            return
    
    print("------------------------------------")
    print("| Failure! Control Plane is wrong! |")
    print("------------------------------------")


if __name__ == "__main__":
    main(sys.argv[1:])