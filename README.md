# cp-testing
CSE599N1 Project 3: Control Plane Testing

# Prerequisites:
- Nothing

# Run:
- python cp-test.py -t topology-file -q traffic-query
    - Example: python cp-test.py -t topo1/network.yml -q topo1/invariants.yml

# Input
- network.yml
    - Network topology
    - YAML format
    - Example: topo1/network.yml 
- invariants.yml
    - Possible generated forwarding rules through BGP process
    - YAML format
    - Example: topo1/invariants.yml

# Output
- Console 
    - Some BGP process including:
        - Advertisements sent and received between switches
        - BGP matchs and actions taken
    - Finally full generated forwarding tables of all switches
    - Answer: control plane is correct or wrong

# Design
- Overall Steps:
    - Build network topology
    - Construct and send all advertisements through the network (BGP advertising)
    - Generate forwarding tables
    - Check if forwarding tables match one case given in query file

- BGP Process:
    - 1) At the very beginning, no switch knows where to send all packages.
    - 2) Several switches begin to send advertisements including "Prefix" (listed in "AdvertisedRoutes"), meaning "All packages with this Prefix can be sent to me".
    - 3) When one switch r2 receives an advertisement from r1, it checks "InboundPolicies", and tries to match the "Prefix" with one policy, if so, take the following actions. The default action of "Allow" would be r2 setting preference of sending Prefix to r1 as 100 (default). Therefore, it knows where to send Prefix in the future.
    - 4) Then, r2 sends this advertisement again to other switches that it connects to, except where it received this advertisement from, which is r1. Before doing so, it checks "OutboundPolicies" and tries to match the policy and take the actions.

- Some design choices:
    - In this project, we simulated BGP process and checked generated forwarding tables.
    - We ignored all Acls in the network since it has nothing to do with BGP advertising.