import random
initial_time = 5
loop = -2
file = open("generic_file.rou.xml","w")
file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
file.write("<routes>\n")

#vehicle_type
file.write('    <vTypeDistribution id="typeVehicleDistribution">\n')
file.write('        <!--http://www.toyota.com.au/prius-v/specifications/prius-v-->\n')                                                                         ### 
file.write('        <vType id="Car" departSpeed="max" accel="3" decel="4.5" length="4.645" width="1.775" height="1.59" maxSpeed="17.88" speedDev="0.1" sigma="0.2" minGap="0.3" probability="0.5"/>\n')
file.write('        <!--hattp://www.rms.nsw.gov.au/business-industry/heavy-vehicles/road-access/general-access-vehicles.html-->\n')
file.write('        <vType id="Truck" accel="3.0" decel="4" length="12.5" width="2.5" height="4.3" maxSpeed="17.88" speedDev="0.1" sigma="0.2" minGap="0.3" probability="0.2"/>\n')
file.write('        <!--hattp://www.modenabus.com/286/119/products/school_bus_school_bus_iveco_9_metres.html-->\n')
file.write('        <vType id="Bus" accel="3.0" decel="4" length="9" width="2.4" height="3.2" maxSpeed="17.88" speedDev="0.1" sigma="0.2" minGap="0.3" probability="0.2"/>\n')
file.write('    </vTypeDistribution>\n')
file.write('\n \n')

while (initial_time<=9000):
    probability= random.randint(1,9)
    loop = loop +2
    final_time = initial_time + 5
    file.write('    <flow id="flow{}" color="0,0,1" begin="{}" probability="0.01{}" type="typeVehicleDistribution">\n         <route edges="110 111"/>\n  </flow>\n' .format(loop, initial_time, probability))

    initial_time = initial_time + 10
file.write('\n')
file.write('</routes>')
file.close()
