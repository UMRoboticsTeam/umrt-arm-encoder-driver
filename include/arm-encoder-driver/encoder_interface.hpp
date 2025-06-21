//
//Created by Toni Odujinrin on 2025-06-21
//
/**
 * @file 
 * Class declaration for EncoderInterface, created to read messages from UMRT's CAN encoders and publish them via Boost signals. 
 */ 


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
#include <unordered_set>
#include <memory>

class EncoderInterface {
public:
    
    EncoderInterface() = default; 
    /**
     * Initializes EncoderInterface channel.
     * @param can_interface can interface of the listening device; defaults to "can0". 
     * @param encoder_can_ids a shared pointer to a unordered_set, that contains the CAN IDs of encoders to listen to.  
     * @param angular_velocity_sample_time device specified angular velocity sampling time.
     */

    EncoderInterface(const std::string& can_interface, std::shared_ptr< const std::unordered_set<uint32_t>> encoder_can_ids, double angular_velocity_sample_time = 0.1 );
    /**
     * Destroys the EncoderInterface channel.
     */
    ~EncoderInterface();

    /**
     * Starts reading the encoder messages and raises boost signal events. 
     */ 
    void begin_read_loop();

  
    /**
     * <a href=https://www.boost.org/doc/libs/1_63_0/doc/html/signals.html>Boost signal</a> 
     * triggered by @ref handle_angle.
     */
    boost::signals2::signal<void(std::uint32_t can_id, double angle, double angular_velocity, std::uint16_t number_of_rotations)> angle_signal;
    /**
     * <a href=https://www.boost.org/doc/libs/1_63_0/doc/html/signals.html>Boost signal</a> 
     * triggered by @ref handle_temp.
     */
    boost::signals2::signal<void(std::uint32_t can_id, double temp)> temp_signal;
    /**
     * <a href=https://www.boost.org/doc/libs/1_63_0/doc/html/signals.html>Boost signal</a> 
     * triggered by @ref handle_all.
     */
    boost::signals2::signal<void(struct can_frame)> verbose_signal;
    /**
     * <a href=https://www.boost.org/doc/libs/1_63_0/doc/html/signals.html>Boost signal</a> 
     * triggered by @ref handle_temp. gives raw(unaltered) values
     */
    boost::signals2::signal<void(std::uint32_t can_id, uint16_t temp_raw)> temp_signal_raw;
    /**
     * <a href=https://www.boost.org/doc/libs/1_63_0/doc/html/signals.html>Boost signal</a> 
     * triggered by @ref handle_angle. gives raw(unaltered) values
     */
    boost::signals2::signal<void(std::uint32_t can_id, uint16_t angle_raw, uint16_t angular_velocity_raw, std::uint16_t number_of_rotations)> angle_signal_raw;

private:
    ifreq ifr{};
    sockaddr_can addr{};

    /**
     * CAN socket descriptor
     */ 
    int can_socket = -1;

    /**
     * device specified angular velocity sampling time.
     */ 
    double m_angular_velocity_sample_time{}; 

    /**
     * unordered_set that contains the CAN IDs of encoders to listen to.  
     */ 
    std::shared_ptr<const std::unordered_set<uint32_t>>m_encoder_can_ids{nullptr}; 
    /**
     * listens to encoder position related messages (number of rotations, anglular velocity, current angle)
     * triggers @ref angle_signal  and @ref angle_signal_raw
     * @param message array pointer to 8-byte CAN massage
     * @param can_id CAN ID of spefic encoder 
     */ 
    void handle_angle(const std::uint8_t* message_data, const std::uint32_t can_id);

    /**
     * listens to encoder temperature values
     * triggers @ref temp_signal  and @ref temp_signal_raw 
     * @param message array pointer to 8-byte CAN massage
     * @param can_id CAN ID of spefic encoder 
     */
    void handle_temp(const std::uint8_t* message_data, const std::uint32_t can_id);

    /**
     * listens to all encoder messages for debug purposes
     * triggers @ref 
     * @param message entire can_frame
     */
    void handle_all(const can_frame& message);
};


#endif //ARM_ENCODER_DRIVER_ENCODER_INTERFACE_HPP