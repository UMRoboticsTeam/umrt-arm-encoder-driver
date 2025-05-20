#include "encoder_interface.hpp"

using std::uint16_t;
using std::uint32_t;
using std::uint8_t;

EncoderInterface::EncoderInterface(const std::string& can_interface, double angular_velocity_sample_time): m_angular_velocity_sample_time(angular_velocity_sample_time)
{
    BOOST_LOG_TRIVIAL(info) << "[+] initializing channel";

    BOOST_LOG_TRIVIAL(info) << "[+] initializing socket";
    can_socket = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (can_socket < 0) {
        BOOST_LOG_TRIVIAL(error) << "[x] could not open socket";
        throw std::runtime_error("[x] could not open socket"); 
    }

    strcpy(ifr.ifr_name, can_interface.c_str());
    BOOST_LOG_TRIVIAL(info) << "[+] fetching interface";
    if (ioctl(can_socket, SIOGIFINDEX, &ifr) < 0) {
        BOOST_LOG_TRIVIAL(error) << "[x] could not find can interface: " << can_interface;
        close(can_socket);
        can_socket = -1;
        throw std::runtime_error("[x] could not find can interface"); 
    }
    BOOST_LOG_TRIVIAL(info) << "[+] binding socket";
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(can_socket, (sockaddr*)&addr, sizeof(addr)) < 0) {
        BOOST_LOG_TRIVIAL(error) << "[x] could not bind socket to can interface";
        close(can_socket);
        can_socket = -1; 
        throw std::runtime_error("[x] could not bind socket to can interface"); 
    }   
    BOOST_LOG_TRIVIAL(info) << "[+] finished initializing channel";
}

EncoderInterface::~EncoderInterface() {
    if (can_socket >= 0) {
        close(can_socket);
        can_socket = -1;
    }
}


void EncoderInterface::begin_read_loop() {
    BOOST_LOG_TRIVIAL(info) << "[+] beginning read loop: ";
    while (true) {
        can_frame message{};
        ssize_t nbytes = read(can_socket, &message, sizeof(can_frame));
        if (nbytes > 0 && message.len == 8) {
            handle_angle(message.data, message.can_id);
            handle_temp(message.data, message.can_id);
            handle_all(message);
        } else {
            BOOST_LOG_TRIVIAL(error) << "[x] invalid data length " << message.len;
        }
    }
};

void EncoderInterface::handle_all(const can_frame& message) {
    verbose_signal(message);
};



void EncoderInterface::handle_angle(const uint8_t* message_data, const uint32_t can_id) {
    if (message_data[0] == 0x55 && message_data[1] == 0x55) {
        uint16_t angle_register_value = static_cast<uint16_t>(message_data[3] << 8) | message_data[2];
        double angle = angle_register_value * 360.0 / 32768; 
        uint16_t angular_velocity_register_value = static_cast<uint16_t>(message_data[5] << 8) | message_data[4];
        double angular_velocity = angular_velocity_register_value * 360.0 / 32768 / m_angular_velocity_sample_time;
        uint16_t number_of_rotations = static_cast<uint16_t>(message_data[7] << 8) | message_data[6];
        angle_signal(can_id, angle, angular_velocity, number_of_rotations);
        angle_signal_raw(can_id, angle_register_value, angular_velocity_register_value, number_of_rotations); 
    }
};

void EncoderInterface::handle_temp(const uint8_t* message_data, const uint32_t can_id) {
    if (message_data[0] == 0x55 && message_data[1] == 0x56) {
        uint16_t temperature_register_value = static_cast<uint16_t>(message_data[3] << 8) | message_data[2];
        int temperature = temperature_register_value / 100;
        temp_signal(can_id, temperature);
        temp_signal_raw(can_id, temperature_register_value); 
    }
};
