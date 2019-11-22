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
- Will be updated soon