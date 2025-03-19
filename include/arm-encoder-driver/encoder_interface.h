#ifndef ENCODER_INTERFACE
#define ENCODER_INTERFACE
#include <boost/log/trivial.hpp>
#include <boost/signals2/signal.hpp>
#include <cstdlib>
#include <fcntl.h>
#include <iostream>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>


#ifdef __linux__ 
    typedef uint8_t __u8;
#endif 


class EncoderInterface {
private:
    
    struct ifreq ifr;
    struct sockaddr_can addr;
    int can_socket;
    uint8_t* previous_data; 



    static volatile int exception_flag;
    void handle_angle(uint8_t* message_data, uint32_t can_id);
    void handle_temp(uint8_t* message_data, uint32_t can_id);
    void handle_all(can_frame message);
    void handle_delta(uint8_t* message_data, uint8_t* previous_data);


public:
    EncoderInterface() = default;
    ~EncoderInterface(); 
    int initialize_channel(const char* can_interface);
    void begin_read_loop();
    boost::signals2::signal<void(uint32_t can_id, double angle, double angular_velocity, uint16_t number_of_rotations)> angle_signal;
    boost::signals2::signal<void(uint32_t can_id, double temp)> temp_signal;
    boost::signals2::signal<void(struct can_frame)> verbose_signal;
};


#endif