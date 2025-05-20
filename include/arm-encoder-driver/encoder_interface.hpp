#ifndef ARM_ENCODER_DRIVER_ENCODER_INTERFACE_HPP
#define ARM_ENCODER_DRIVER_ENCODER_INTERFACE_HPP
#include <boost/log/trivial.hpp>
#include <boost/signals2/signal.hpp>
#include <cstdint>
#include <cstdlib>
#include <fcntl.h>
#include <iostream>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <cstring>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>
#include <stdexcept>
#include <cerrno>

class EncoderInterface {
public:
    

    EncoderInterface(const std::string& can_interface, double angular_velocity_sample_time = 0.1);
    ~EncoderInterface();
    void begin_read_loop();
    boost::signals2::signal<void(std::uint32_t can_id, double angle, double angular_velocity, std::uint16_t number_of_rotations)> angle_signal;
    boost::signals2::signal<void(std::uint32_t can_id, double temp)> temp_signal;
    boost::signals2::signal<void(struct can_frame)> verbose_signal;
    boost::signals2::signal<void(std::uint32_t can_id, uint16_t temp_raw)> temp_signal_raw;
    boost::signals2::signal<void(std::uint32_t can_id, uint16_t angle_raw, uint16_t angular_velocity_raw, std::uint16_t number_of_rotations)> angle_signal_raw;

private:
    ifreq ifr{};
    sockaddr_can addr{};
    int can_socket = -1;
    double m_angular_velocity_sample_time{}; 

    void handle_angle(const std::uint8_t* message_data, const std::uint32_t can_id);
    void handle_temp(const std::uint8_t* message_data, const std::uint32_t can_id);
    void handle_all(const can_frame& message);
};


#endif //ARM_ENCODER_DRIVER_ENCODER_INTERFACE_HPP