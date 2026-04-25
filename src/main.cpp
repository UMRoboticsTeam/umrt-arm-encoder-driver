#include "encoder_interface.hpp"
#include <boost/signals2/slot.hpp>
#include <iostream>

using std::uint16_t;
using std::uint32_t;

static const char DEFAULT_CAN_DEVICE[] = "can0";

void temperature_handler(uint32_t can_id, double temp) {
    BOOST_LOG_TRIVIAL(info) << "can_id: " << can_id << " temp: " << temp << "\n";
};
void angle_handler(uint32_t can_id, uint16_t angle, uint16_t angular_vel, int16_t n_rotations) {
    BOOST_LOG_TRIVIAL(info) << "can_id: " << can_id <<" angle: " <<angle<<" velocity: " << angular_vel << " num rotations: " << n_rotations << "\n";
};


int main(int argc, char** argv) {
    // Grab interface name from the CLI if it was provided, otherwise default to can0
    std::string can_interface = DEFAULT_CAN_DEVICE;
    if (argc > 1) {
        can_interface = argv[1];
    }

    auto encoder_can_ids = std::make_shared<const std::unordered_set<uint32_t>>(std::initializer_list<uint32_t>{});

    // Create encoder
    EncoderInterface encoder(can_interface, encoder_can_ids);

    // Set up signal handlers
    encoder.angle_signal.connect([](uint32_t can_id, int16_t angle, uint16_t angular_vel, uint16_t n_rotations) { angle_handler(can_id, angle, angular_vel, n_rotations); });
    encoder.temp_signal.connect([](uint32_t can_id, double temp) { temperature_handler(can_id, temp); });

    // Start receiving CAN messages
    encoder.begin_read_loop();

    return 0;
};
