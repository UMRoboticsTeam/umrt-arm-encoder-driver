#include "encoder_interface.hpp"
#include <boost/signals2/slot.hpp>
#include <iostream>

using std::uint16_t;
using std::uint32_t;

void temperature_handler(uint32_t can_id, uint16_t temp) {
    BOOST_LOG_TRIVIAL(info) << "can_id: " << can_id << " temp: " << temp << "\n";
};
void angle_handler(uint32_t can_id, uint16_t angle, uint16_t angular_vel, uint16_t n_rotations) {
    BOOST_LOG_TRIVIAL(info) << "can_id: " << can_id <<" angle: " <<angle<<" velocity: " << angular_vel << " num rotations: " << n_rotations << "\n";
};


int main(int argc, char** argv) {
    

    // Grab interface name from the CLI if it was provided, otherwise default to can0
    std::string can_interface = "can0";
    if (argc > 1) {
        can_interface = argv[1];
    }

    std::shared_ptr<const std::unordered_set<uint32_t>> encoder_can_ids = std::make_shared<const std::unordered_set<uint32_t>>(std::initializer_list<uint32_t>{}); 

    //initial can interface 
    EncoderInterface myInterface(can_interface, encoder_can_ids);

    //set up signal handlers
    myInterface.angle_signal.connect([](uint32_t can_id, uint16_t angle, uint16_t angular_vel, uint16_t n_rotations) { angle_handler(can_id, angle, angular_vel, n_rotations); });
    myInterface.temp_signal.connect([](uint32_t can_id, uint16_t temp) { temperature_handler(can_id, temp); });

    myInterface.begin_read_loop();

    return 0;
};
