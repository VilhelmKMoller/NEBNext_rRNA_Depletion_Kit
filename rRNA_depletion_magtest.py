from opentrons import protocol_api
import time
"""
Make pippetting protocol using OpenTrons with NEBNext Depletion Kit(bacteria)
Used for removing ribonsomal RNA from mRNA sample.

Version 1
owner: Vilhelm
date: 2021.01.26

URL for kit: https://international.neb.com/products/e7850-nebnext-rrna-depletion-kit-bacteria#Product%20Information


Optimizations:
- Find a way to use a 8 channel pippette(i guess you can have an 1 and 8 channel pippette)


Questions
- What is the biggest volumn pippetted?(This will decide what size pippettes we will use)

Comments:
- The system is testing. So all stock solutions from the kit are added to PCR tubes and inserted into
the aluminum heating block. This is done to avoid wide spread contamination of reagents. (if it is a problem)
"""


## 1. metadata
metadata = {
    'protocolName': 'rRNA Depletion',
    'author': 'Name <vikmol@biosustain.dtu.dk>',
    'description': 'RNA purification using NEBNext Depletion Kit(bacteria)',
    'apiLevel': '2.8'
}

## 2. protocol run function. the part after the colon lets your editor know
# where to look for autocomplete suggestions
def run(protocol: protocol_api.ProtocolContext):

    ## 3. labware
    # labware names: https://labware.opentrons.com/
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    #sample_plate = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', '11')
    #reagents_plate = protocol.load_labware('opentrons_24_aluminumblock_generic_2ml_screwcap', '9')


    # modules
    # Load a Magnetic Module GEN2 in deck slot 1.
    magnetic_module = protocol.load_module('magnetic module', '1')
    # define plate on Magnetic Module
    mag_plate = magnetic_module.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    # temperature module
    temp_mod = protocol.load_module('temperature module', '4')
    temp_plate = temp_mod.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul')

    # Thermocycler module
    tc_mod = protocol.load_module('Thermocycler Module') ## OPS OPS DONT KNOW IF I NEED TO SECIFICY POSITION '7 and 12'
    tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    ## 4. pipettes
    # tips
    tip_rack_20_1 = protocol.load_labware('opentrons_96_filtertiprack_20ul', '5')
    tip_rack_300_1 = protocol.load_labware('opentrons_96_tiprack_300ul', '6')
    tip_rack_300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', '9')

    #tip_rack_20_2 = protocol.load_labware('opentrons_96_filtertiprack_20ul', '4')
    pipette_single = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tip_rack_20_1])
    pipette_multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tip_rack_300_1, tip_rack_300_2])
    
    #opentrons.protocol_api.contexts.MagneticModuleContext(ctx: ProtocolContext, hw_module: modules.magdeck.MagDeck, geometry: ModuleGeometry, at_version: APIVersion, loop: asyncio.AbstractEventLoop)
    
    ### Initiating modules

    ## open thermocyler and set temperature to 4C
    tc_mod.open_lid()
    tc_mod.set_block_temperature(4)

    ## Lower magnets in magnetic module
    magnetic_module.disengage()

    ## set temp_mod to 4C
    temp_mod.set_temperature(4)


    ### Liquid positions:
    ## reservoir
    beads = reservoir['A2']
    ethanol80 = reservoir['A3']
    liquid_waste = reservoir['A11']
    # cooMagneticModuleContextling block(given in rows!)

    # input sample set to 1ug RNA concentration.
    rRNA_depleation_enzyme = temp_plate['A5']
    rRNA_depleation_buffer = temp_plate['B5']
    RNaseH_enzyme = temp_plate['C5']
    RNaseH_buffer = temp_plate['D5']
    DNaseI_enzyme = temp_plate['E5']
    DNaseI_buffer = temp_plate['F5']
    nfH2O = temp_plate['G5']

    #samples A1-E1(first row). starts in PCR. sample vol is 11uL

    
    ## 5. commands
    sample_nr = 8
    
    ## OPS OPS CHANGE TO DO WELLSS INSTEAD OF ROWS!!!!
    # add the rRNA_depleation_buffer buffer to each sample in thermocyler(start A1, pr row)
    pipette_single.pick_up_tip()
    for i in range(sample_nr):
        #pipette_single.distribute(2, rRNA_depleation_buffer, tc_plate.rows()[i])
        pipette_single.distribute(2, rRNA_depleation_buffer, tc_plate.wells()[i], new_tip='never')
    pipette_single.drop_tip()
    # add the rRNA_depleation_enzyme buffer to each sample in thermocyler(start A1, pr row)
    for i in range(sample_nr):
        #pipette_single.distribute(2, rRNA_depleation_enzyme, tc_plate.rows()[i])
        pipette_single.distribute(2, rRNA_depleation_enzyme, tc_plate.wells()[i])

    ## OPS OPS CHANGE TO LOOP INSTEAD OF SINGLE
    # mix using p300_multi channel
    pipette_multi.pick_up_tip()
    #pipette_single.mix(3, 20)
    pipette_multi.mix(10, 20, tc_plate['A1']) # mix 10 times, volumne=20uL, 0='A1'
    pipette_multi.drop_tip()
    
    
    # close lid
    tc_mod.close_lid()
    # set lid temp to 105C
    tc_mod.set_lid_temperature(105) #105
    # set thermocyler temp to 95C and hold for 2 min
    start_temp = 95
    tc_mod.set_block_temperature(start_temp, hold_time_seconds=120, block_max_volume=15)
    # ramp down to temp 22C
    while start_temp > 22:
        #tc_mod.set_block_temperature(22, hold_time_seconds=2, ramp_rate=0.1, block_max_volume=15) # OPS OPS chaning the ramp rate can give problems!!!
        start_temp = round(start_temp - 0.1, 1)
        tc_mod.set_block_temperature(start_temp, hold_time_seconds=1, block_max_volume=15)
        #print(start_temp)
        #time.sleep(1)

    # run at 22C for 5min(300s)
    tc_mod.set_block_temperature(22, hold_time_seconds=300, block_max_volume=15) #300
    # open lid
    tc_mod.open_lid()
    

    # set temp back to 4C
    tc_mod.set_block_temperature(4)
    
    # add the RNaseH_buffer buffer to each sample in thermocyler(start A1, pr row)
    for i in range(sample_nr):
        pipette_single.distribute(2, RNaseH_buffer, tc_plate.wells()[i])
    # add the RNaseH_enzyme buffer to each sample in thermocyler(start A1, pr row)
    for i in range(sample_nr):
        pipette_single.distribute(2, RNaseH_enzyme, tc_plate.wells()[i])
    # add Nuclease free water
    for i in range(sample_nr):
        pipette_single.distribute(1, nfH2O, tc_plate.wells()[i])

    # should be a for loop if you run more than 8 samples
    # mix using p300_multi channel
    pipette_multi.pick_up_tip()
    #pipette_single.mix(3, 20)
    pipette_multi.mix(10, 25, tc_plate['A1']) # mix 10 times, volumne=25uL, 0='A1'
    pipette_multi.drop_tip()
    




    

    # close lid
    tc_mod.close_lid()
    # set lid temp to 55C
    tc_mod.set_lid_temperature(55)
    # set thermocyler temp to 50C and hold for 30 min
    tc_mod.set_block_temperature(50, hold_time_seconds=1800, block_max_volume=20)
    # open lid
    tc_mod.open_lid()

    # set temp back to 4C
    tc_mod.set_block_temperature(4)
    # add the RNaseH_buffer buffer to each sample in thermocyler(start A1, pr row)
    for i in range(sample_nr):
        pipette_single.distribute(5, DNaseI_buffer, tc_plate.wells()[i])
    # add the RNaseH_enzyme buffer to each sample in thermocyler(start A1, pr row)
    for i in range(sample_nr):
        pipette_single.distribute(2.5, DNaseI_enzyme, tc_plate.wells()[i])
    # add Nuclease free water
    for i in range(sample_nr):
        pipette_single.distribute(22.5, nfH2O, tc_plate.wells()[i])

    # should be a for loop if you run more than 8 samples
    # mix using p300_multi channel
    pipette_multi.pick_up_tip()
    #pipette_single.mix(3, 20)
    pipette_multi.mix(10, 55, tc_plate['A1'])
    pipette_multi.drop_tip()

    # close lid
    tc_mod.close_lid()
    # set lid temp to 40C
    tc_mod.set_lid_temperature(40)
    # set thermocyler temp to 37C and hold for 30 min
    tc_mod.set_block_temperature(37, hold_time_seconds=1800, block_max_volume=50)
    # open lid
    tc_mod.open_lid()

    # set temp back to 4C
    tc_mod.set_block_temperature(4)

    ## MAKE SURE YOU MIX THE BEADS 10 time before you adde them! Do it with max vol 300ul
    # should be a for loop if you run more than 8 samples
    # add beads using p300_multi channel
    pipette_multi.pick_up_tip()
    #pipette_single.mix(3, 20)
    pipette_multi.mix(10, 20)
    #pipette_multi.distribute(90, beads, tc_plate['A1'])
    pipette_multi.aspirate(90, beads)
    pipette_multi.dispense(90, tc_plate['A1'])
    pipette_multi.mix(10, 20)
    pipette_multi.drop_tip()

    # incubate: wait for the RNA to bind for 15 min:
    protocol.delay(minutes=15)

    # pipette everything in the thermocyler and aspirate it into the magnetic plate.
    pipette_multi.distribute(141, tc_plate.wells()[0], mag_plate.wells()[0])
    
    # inage the magnetic rack to seperate the beads:
    magnetic_module.engage()
    # HIGHT SHOULD BE SET CORRECTLY I JUST DONT KNOW WHAT IT IS

    # incubate: wait for magnets to seperate the RNA from the liquid
    protocol.delay(minutes=3) # i assume 3 min is good?

    # remove liquid from magnetic plate.
    # THIS SHOULD BE DONE VERY SLOWLY FIND WAY TO SUCK VERY SLOWLY!!!
    pipette_multi.distribute(145, mag_plate.wells()[0], liquid_waste)

    # add ethanol80 to magnetic plate.
    # THIS SHOULD BE DONE VERY SLOWLY FIND WAY TO SUCK VERY SLOWLY!!!
    pipette_multi.distribute(200, ethanol80, mag_plate.wells()[0])

    # incubate: wait for 30 sec
    protocol.delay(seconds=30)

    # remove liquid from magnetic plate.
    # THIS SHOULD BE DONE VERY SLOWLY FIND WAY TO SUCK VERY SLOWLY!!!
    pipette_multi.distribute(201, mag_plate.wells()[0], liquid_waste)

    # Repate the the step above
    # add ethanol80 to magnetic plate.
    # THIS SHOULD BE DONE VERY SLOWLY FIND WAY TO SUCK VERY SLOWLY!!!
    pipette_multi.distribute(200, ethanol80, mag_plate.wells()[0])
    # incubate: wait for 30 sec
    protocol.delay(seconds=30)
    # remove liquid from magnetic plate.
    # THIS SHOULD BE DONE VERY SLOWLY FIND WAY TO SUCK VERY SLOWLY!!!
    pipette_multi.distribute(201, mag_plate.wells()[0], liquid_waste)

    # dry the beads.
    protocol.delay(minutes=4) # 5 min is max

    # add Nuclease free water to
    for i in range(sample_nr):
        pipette_single.distribute(7, nfH2O, mag_plate.wells()[i])
    # mix with multi pipette
    pipette_multi.pick_up_tip()
    pipette_multi.mix(10, 10, mag_plate['A1'])
    pipette_multi.drop_tip()

    ####################### ADD THE REST LATER #######################
    # incubate for 2 min så RNA can desasociate from beads
    protocol.delay(minutes=2)

    # NOW place in the magnetic rack again to compleatly seperate
    protocol.delay(minutes=3)

    # extract 5 ul until collection tubes

    