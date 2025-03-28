#ifndef ENCODER_INTERFACE
#define ENCODER_INTERFACE
#include <boost/log/trivial.hpp>
#include <boost/signals2/signal.hpp>
#include <cstdint>
#include <cstdlib>
#include <fcntl.h>
#include <iostream>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

class EncoderInterface {
public:
    EncoderInterface() = default;
    ~EncoderInterface();
    int initialize_channel(const char* can_interface);
    void begin_read_loop();
    boost::signals2::signal<void(std::uint32_t can_id, double angle, double angular_velocity, std::uint16_t number_of_rotations)> angle_signal;
    boost::signals2::signal<void(std::uint32_t can_id, double temp)> temp_signal;
    boost::signals2::signal<void(struct can_frame)> verbose_signal;

private:
    ifreq ifr{};
    sockaddr_can addr{};
    int can_socket = 0;

    void handle_angle(const std::uint8_t* message_data, const std::uint32_t can_id);
    void handle_temp(const  std::uint8_t* message_data, const std::uint32_t can_id);
    void handle_all(const can_frame & message);
};


#endif