import copy
class gate:
    def __init__(self, name, p, g, b, intr, gamma=1):
        self.name = name
        self.p = p
        self.g = g
        self.b = b
        self.h = 0
        self.gamma = gamma
        self.intr = intr

    def get_effective_intr(self):
        return self.intr * self.gamma

    def __str__(self):
        return f"\n\t{self.name} -> | GAMMA: {self.gamma} | \t\tp: {self.p}, g: {self.g}, b: {self.b}";

    def __repr__(self):
        return self.__str__()


class load:
    def __init__(self, load):
        self.load = load

    def __str__(self):
        return f"\n\tLoad: {self.load}";

    def __repr__(self):
        return self.__str__()


def nand2(b=1, gamma=1):
    return gate("nand2", 2, 4.0 / 3, b, 4, gamma)


def nor2(b=1, gamma=1):
    return gate("nor2", 2, 5.0 / 3, b, 5, gamma)


def inv(b=1, gamma=1):
    return gate("inv", 1, 1, b, 3, gamma)


def set_h(circuit_: list, with_sizing=True):
    '''
        Computes iteratively the internal electrical effort H of a gate as the ratio between 
        its output load and its internal load that it presents to the previous gate
    '''
    circuit = copy.deepcopy(circuit_)
    assert (type(circuit[-1]) == load) # To make sure we have a final load
    post_g = circuit[-1].load
    for i in range(len(circuit) - 2, -1, -1): # From second-to-last to 0
        gate = circuit[i]
        #NOTE: how do we handle intermediate loads for H computation??
        if type(gate) == load: # If we have intermediate loads we skip it for now
            continue
        # Optionally we consider the beta of the gate when computing its intrinsic load
        gate.h = post_g / gate.get_effective_intr() if with_sizing else post_g / gate.intr
        post_g = gate.get_effective_intr() if with_sizing else gate.intr
    return circuit


def compute_min_delay(circuit_: list):
    circuit = copy.deepcopy(circuit_)
    P = 0
    H = 1
    G = 1
    B = 1
    circuit = set_h(circuit, with_sizing=False)
    length = len([g for g in circuit if type(g) != load]) # We compute how many stages we have excluding loads
    for gate in reversed(circuit[:-1]):
        #NOTE: how do we handle intermediate load when computing delay?
        if type(gate) == load: continue
        P += gate.p
        H *= gate.h
        G *= gate.g
        B *= gate.b
    return P + length * (G * H * B) ** (1.0 / length)


def compute_curr_delay(circuit_: list):
    circuit = copy.deepcopy(circuit_)
    P = 0
    GHB = 0
    circuit = set_h(circuit, with_sizing=True)
    for gate in reversed(circuit[:-1]):
        #NOTE: how do we handle intermediate load when computing delay?
        if type(gate) == load: continue
        P += gate.p
        GHB += (gate.h * gate.b * gate.g)
    return P + GHB


def perform_sizing(circuit_: list, clamp_to_1 = False):
    circuit = copy.deepcopy(circuit_)
    assert len([g for g in circuit if type(g) == load]) == 1 and type(circuit[-1]) == load
    P = 0
    H = 1
    G = 1
    B = 1
    circuit = set_h(circuit, with_sizing=False)
    length = len(circuit) - 1  # final load not counted
    for gate in reversed(circuit[:-1]):
        P += gate.p
        H *= gate.h
        G *= gate.g
        B *= gate.b
    GHB = G * H * B
    f_cap = GHB ** (1.0 / (length))
    prev_gate = circuit[0]
    for gate in circuit[1:-1]:
        gate.gamma = prev_gate.gamma * f_cap / (prev_gate.b * gate.g)
        if gate.gamma < 1 and clamp_to_1:gate.gamma = 1.0
        prev_gate = gate
    return circuit

def perform_sizing_intermediate_load(circuit_: list, clamp_to_1 = False):
    circuit = copy.deepcopy(circuit_)
    count = 0
    circ_no_int = [] # Contains the entire circuit without intermediate load
    for g in circuit:
        if type(g) == load:
            count += 1 # Just to count how many intermediate loads we have 
        else:
            circ_no_int.append(g)
    assert count == 2 and type(circuit[-1]) == load 
    circ_no_int.append(circuit[-1])  # We add the final load
    circ_no_int = perform_sizing(circ_no_int, clamp_to_1) # Sizes as if no intermediate cap was there the entire circuit
    circ_a_b = []  # Contains the first part only until the intermediate load
    temp = 0
    for i in range(len(circuit)):
        if type(circuit[i]) != load:
            circ_a_b.append(circ_no_int[i]) # We append the gate
            circ_no_int[i].gamma = 1 # We reset the gamma
        else:
            # When we reach the intermediate load we stop and we add a load that considers the int. load and branching load
            circ_a_b.append(load(circuit[i].load + circuit[i - 1].b * circ_no_int[i].get_effective_intr()))
            temp = i
            break
    old_b = circ_a_b[-2].b
    circ_a_b[-2].b = 1 # We have swapped out the potential branch load and therefore we have branching of 1 now (It will be restored later)
    circuit = perform_sizing(circ_a_b, clamp_to_1) # We size the first part only
    circuit.extend(circ_no_int[temp:]) # We add the rest of the circuit that we had sized before
    for i in range(len(circuit)):
        if type(circuit[i]) == load:
            circuit[i-1].b = old_b # I restore the correct branching effort in the final circuit
            break
    return circuit


print(
        "------- 4X PREDECODER WITH INTERMEDIATE LOAD------------------------------------------------------------------\n")
first_part = [inv(), inv(b=2), nand2(), inv(b=4), nand2(), inv(b=16), load(228.72), nand2(), inv(), load(66.06)]
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first) # DONT TRUST THIS VALUE IT HAS NO MEANING
print()
print("CURR_DELAY:", compute_curr_delay(first_part))
first_part_sized = perform_sizing_intermediate_load(first_part, True)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:", first_part_sized)

print(
        "------- 2X PREDECODER WITH INTERMEDIATE LOAD------------------------------------------------------------------\n")
first_part = [inv(), inv(b=2), nand2(), inv(b=64), load(228.72), nand2(), inv(), nand2(), inv(), load(66.06)]
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:", compute_curr_delay(first_part))
first_part_sized = perform_sizing_intermediate_load(first_part, True)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:", first_part_sized)

print(
        "------- 1X PREDECODER WITH INTERMEDIATE LOAD------------------------------------------------------------------\n")
first_part = [inv(), inv(b=128), load(228.72), nand2(), inv(), nand2(), inv(), nand2(), inv(), load(66.06)]
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:", compute_curr_delay(first_part))
first_part_sized = perform_sizing_intermediate_load(first_part, True)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:", first_part_sized)


'''
circ = [inv(), nand2(), nor2(), inv(), load(256.0 * 16.0 / 60.0)]
print(circ)
print("MIN_DELAY:",compute_min_delay(circ))
print("CURR_DELAY:",compute_curr_delay(circ))
circ_sized = perform_sizing(circ)
print(circ_sized)
print("AFTER_SIZING:", compute_curr_delay(circ_sized))


print("\n\n\n")

circ = [nand2(b=2), nand2(b=3), nand2(b=1), load(18.0)]
print("MIN_DELAY:",compute_min_delay(circ))
print("CURR_DELAY:",compute_curr_delay(circ))
circ_sized = perform_sizing(circ)
print(circ_sized)
print("AFTER_SIZING:", compute_curr_delay(circ_sized))

print("------- 4X PREDECODER ------------------------------------------------------------------\n")
first_part = [inv(), inv(b=2), nand2(), inv(b=4), nand2(), inv(), load(292.72)]
print("------------------- FIRST_PART: ---------------------------------------\n\n")
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:", compute_curr_delay(first_part))
first_part_sized = perform_sizing(first_part)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:", first_part_sized)

print("\n\n-------------------- SECOND PART: ---------------------------------------\n\n")
second_part = [nand2(), inv(), load(66.06)]
min_del_second = compute_min_delay(second_part)
print("MIN_DELAY:", min_del_second)
print()
print("CURR_DELAY:", compute_curr_delay(second_part))
second_part_sized = perform_sizing(second_part)
print("AFTER_SIZING:", compute_curr_delay(second_part_sized))
print("\nCIRCUIT:", second_part_sized)
print("\n\nTOT_MIN_DELAY:", min_del_first + min_del_second)

print("-------2X PREDECODER -----------------------------------------------------------------------------------\n")
first_part = [inv(), inv(b=2), nand2(), inv(), load(484.72)]
print("--------------------FIRST_PART: ---------------------------------------\n\n")
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:", compute_curr_delay(first_part))
first_part_sized = perform_sizing(first_part)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:", first_part_sized)

print("\n\nSECOND: ---------------------------------------\n\n")
second_part = [nand2(), inv(), nand2(), inv(), load(66.06)]
min_del_second = compute_min_delay(second_part)
print("MIN_DELAY:", min_del_second)
print()
print("CURR_DELAY:", compute_curr_delay(second_part))
second_part_sized = perform_sizing(second_part)
print("AFTER_SIZING:", compute_curr_delay(second_part_sized))
print("\nCIRCUIT:", second_part_sized)
print("\n\nTOT_MIN_DELAY:", min_del_first + min_del_second)

print("-------1X PREDECODER -----------------------------------------------------------------------------------\n")
first_part = [inv(), inv(), load(740.72)]
print("--------------------FIRST_PART: ---------------------------------------\n\n")
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:", compute_curr_delay(first_part))
first_part_sized = perform_sizing(first_part)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:", first_part_sized)

print("\n\nSECOND: ---------------------------------------\n\n")
second_part = [nand2(), inv(), nand2(), inv(), nand2(), inv(), load(66.06)]
min_del_second = compute_min_delay(second_part)
print("MIN_DELAY:", min_del_second)
print()
print("CURR_DELAY:", compute_curr_delay(second_part))
second_part_sized = perform_sizing(second_part)
print("AFTER_SIZING:", compute_curr_delay(second_part_sized))
print("\nCIRCUIT:", second_part_sized)

print("\n\nTOT_MIN_DELAY:", min_del_first + min_del_second)
'''
