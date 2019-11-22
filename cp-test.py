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


    '''
    # build the query plan
    query_plan = []
    try:
        with open(query_file, 'r') as f:
            data = yaml.safe_load(f)
            # build_plan(data, query_plan)
    except IOError:
        print(query_file + " doesn't existed!")
        sys.exit()

    print("finish!")
    '''


if __name__ == "__main__":
    main(sys.argv[1:])