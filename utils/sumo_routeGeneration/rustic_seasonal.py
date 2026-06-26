import random

def generate_generic_route_file(
    output_file="generic_file.rou.xml",
    initial_time=5,
    end_time=9000,
    time_step=10,
    flow_duration=5,
    initial_flow_id=-2,
):
    """
    Generate a generic SUMO route file with randomized vehicle flow probabilities.

    This function creates a SUMO `.rou.xml` route file containing a vehicle type
    distribution for cars, trucks, and buses. It then generates multiple traffic
    flows over a specified time interval. Each flow uses the same route and a
    randomized probability value.

    Args:
        output_file: Name or path of the SUMO route file to be generated.
            Defaults to ``"generic_file.rou.xml"``.
        initial_time: Initial departure time for the first generated flow.
            Defaults to 5.
        end_time: Maximum simulation time used to stop generating flows.
            Defaults to 9000.
        time_step: Time interval between consecutive generated flows.
            Defaults to 10.
        flow_duration: Duration of each generated flow. Defaults to 5.
        initial_flow_id: Initial flow identifier offset. The function increments
            this value by 2 before writing each flow. Defaults to -2.

    Returns:
        None. The function writes the generated route data directly to the
        specified output file.
    """
    flow_id = initial_flow_id

    with open(output_file, "w", encoding="utf-8") as file:
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file.write("<routes>\n")

        file.write('    <vTypeDistribution id="typeVehicleDistribution">\n')
        file.write('        <!--http://www.toyota.com.au/prius-v/specifications/prius-v-->\n')
        file.write(
            '        <vType id="Car" departSpeed="max" accel="3" decel="4.5" '
            'length="4.645" width="1.775" height="1.59" maxSpeed="17.88" '
            'speedDev="0.1" sigma="0.2" minGap="0.3" probability="0.5"/>\n'
        )
        file.write(
            '        <!--http://www.rms.nsw.gov.au/business-industry/heavy-vehicles/'
            'road-access/general-access-vehicles.html-->\n'
        )
        file.write(
            '        <vType id="Truck" accel="3.0" decel="4" length="12.5" '
            'width="2.5" height="4.3" maxSpeed="17.88" speedDev="0.1" '
            'sigma="0.2" minGap="0.3" probability="0.2"/>\n'
        )
        file.write(
            '        <!--http://www.modenabus.com/286/119/products/'
            'school_bus_school_bus_iveco_9_metres.html-->\n'
        )
        file.write(
            '        <vType id="Bus" accel="3.0" decel="4" length="9" '
            'width="2.4" height="3.2" maxSpeed="17.88" speedDev="0.1" '
            'sigma="0.2" minGap="0.3" probability="0.2"/>\n'
        )
        file.write("    </vTypeDistribution>\n")
        file.write("\n\n")

        current_time = initial_time

        while current_time <= end_time:
            probability = random.randint(1, 9)
            flow_id += 2
            final_time = current_time + flow_duration

            file.write(
                '    <flow id="flow{}" color="0,0,1" begin="{}" '
                'probability="0.01{}" type="typeVehicleDistribution">\n'
                '        <route edges="110 111"/>\n'
                '    </flow>\n'.format(flow_id, current_time, probability)
            )

            current_time += time_step

        file.write("\n")
        file.write("</routes>")


if __name__ == "__main__":
    generate_generic_route_file()