class gate:
    def __init__(self, name, p, g, b, intr, gamma = 1):
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
        return f"\n\tLoad: {self.load}\n";

    def __repr__(self):
        return self.__str__()

def nand2(b = 1,gamma=1):
    return gate("nand2", 2,4.0/3,b,4,gamma)

def nor2(b = 1,gamma=1):
    return gate("nor2", 2,5.0/3,b,5,gamma)

def inv(b = 1,gamma=1):
    return gate("inv", 1,1,b,3,gamma)

def set_h(circuit: list, with_sizing = True):
    assert(type(circuit[-1]) == load)
    post_g = circuit[-1].load
    for i in range(len(circuit) - 2, -1, -1):
        gate = circuit[i]
        gate.h = post_g / gate.get_effective_intr() if with_sizing else post_g / gate.intr
        post_g = gate.get_effective_intr() if with_sizing else gate.intr

def compute_min_delay(circuit: list):
    P = 0
    H = 1
    G = 1
    B = 1
    set_h(circuit, with_sizing=False)
    length = len(circuit) - 1 # final load not counted
    for gate in reversed(circuit[:-1]):
        P += gate.p
        H *= gate.h
        G *= gate.g
        B *= gate.b
    return P + length * (G * H * B) ** (1.0/length)

def compute_curr_delay(circuit: list):
    P = 0
    GHB = 0
    set_h(circuit, with_sizing=True)
    length = len(circuit) - 1 # final load not counted
    for gate in reversed(circuit[:-1]):
        P += gate.p
        GHB += (gate.h * gate.b * gate.g)
    return P + GHB

def perform_sizing(circuit: list):
    assert len([g for g in circuit if type(g) == load]) == 1
    P = 0
    H = 1
    G = 1
    B = 1
    set_h(circuit, with_sizing=False)
    length = len(circuit) - 1 # final load not counted
    for gate in reversed(circuit[:-1]):
        P += gate.p
        H *= gate.h
        G *= gate.g
        B *= gate.b
    GHB = G*H*B
    f_cap = GHB ** (1.0/(length))
    prev_gate = circuit[0]
    for gate in circuit[1:-1]:
        gate.gamma = prev_gate.gamma * f_cap / (prev_gate.b * gate.g)
        prev_gate = gate

    return circuit

def perform_sizing_intermediate_load(circuit: list):
    count = 0
    circ_no_int = []
    for g in circuit:
        if type(g) == load:
            count += 1
        else:
            circ_no_int.append(g)
    assert count == 2
    # Sizes as if no intermediate cap was there
    circ_no_int = perform_sizing(circ_no_int) 
    circ_a_b = []
    temp = 0
    for i in range(len(circuit)):
        if type(circuit[i]) != load:
            circ_a_b.append(circ_no_int[i])
        else:
            circ_a_b.append(load(circuit[i] + circuit[i-1].b * circ_no_int[i].get_effective_intr()))
            temp = i
            break
    circuit = perform_sizing(circ_a_b)
    circuit.extend(circ_no_int[i:])
    return circuit




#NOTE: there must be a final load
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
'''

print("------- 4X PREDECODER ------------------------------------------------------------------\n")
first_part = [inv(), inv(b=2), nand2(), inv(b=4), nand2(), inv(), load(292.72)]
print("------------------- FIRST_PART: ---------------------------------------\n\n")
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:",compute_curr_delay(first_part))
first_part_sized = perform_sizing(first_part)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:",first_part_sized)

print("\n\n-------------------- SECOND PART: ---------------------------------------\n\n")
second_part = [nand2(), inv(), load(66.06)]
min_del_second = compute_min_delay(second_part)
print("MIN_DELAY:",min_del_second)
print()
print("CURR_DELAY:",compute_curr_delay(second_part))
second_part_sized = perform_sizing(second_part)
print("AFTER_SIZING:", compute_curr_delay(second_part_sized))
print("\nCIRCUIT:",second_part_sized)
print("\n\nTOT_MIN_DELAY:", min_del_first + min_del_second)


print("-------2X PREDECODER -----------------------------------------------------------------------------------\n")
first_part=[inv(), inv(b=2), nand2(), inv(), load(484.72)]
print("--------------------FIRST_PART: ---------------------------------------\n\n")
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:",compute_curr_delay(first_part))
first_part_sized = perform_sizing(first_part)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:",first_part_sized)

print("\n\nSECOND: ---------------------------------------\n\n")
second_part=[nand2(), inv(), nand2(), inv(), load(66.06)]
min_del_second = compute_min_delay(second_part)
print("MIN_DELAY:",min_del_second)
print()
print("CURR_DELAY:",compute_curr_delay(second_part))
second_part_sized = perform_sizing(second_part)
print("AFTER_SIZING:", compute_curr_delay(second_part_sized))
print("\nCIRCUIT:",second_part_sized)
print("\n\nTOT_MIN_DELAY:", min_del_first + min_del_second)

print("-------1X PREDECODER -----------------------------------------------------------------------------------\n")
first_part=[inv(), inv(), load(740.72)]
print("--------------------FIRST_PART: ---------------------------------------\n\n")
min_del_first = compute_min_delay(first_part)
print("MIN_DELAY:", min_del_first)
print()
print("CURR_DELAY:",compute_curr_delay(first_part))
first_part_sized = perform_sizing(first_part)
print("AFTER_SIZING:", compute_curr_delay(first_part_sized))
print("\nCIRCUIT:",first_part_sized)

print("\n\nSECOND: ---------------------------------------\n\n")
second_part=[nand2(), inv(), nand2(), inv(), nand2(), inv(), load(66.06)]
min_del_second = compute_min_delay(second_part)
print("MIN_DELAY:",min_del_second)
print()
print("CURR_DELAY:",compute_curr_delay(second_part))
second_part_sized = perform_sizing(second_part)
print("AFTER_SIZING:", compute_curr_delay(second_part_sized))
print("\nCIRCUIT:",second_part_sized)

print("\n\nTOT_MIN_DELAY:", min_del_first + min_del_second)
