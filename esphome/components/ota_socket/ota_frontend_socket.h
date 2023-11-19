#pragma once

#include "esphome/core/component.h"
#include "esphome/components/ota/ota_frontend.h"
#include "esphome/components/socket/socket.h"

namespace esphome {
namespace ota_socket {

/// OTAComponent provides a simple way to integrate Over-the-Air updates into your app using ArduinoOTA.
class OTAFrontendSocket : public Component, public ota::OTAFrontend {
 public:
  OTAFrontendSocket();

  /// Manually set the port OTA should listen on.
  void set_port(uint16_t port);

  ssize_t read(uint8_t *buf, size_t len) override;
  ssize_t write(const uint8_t *buf, size_t len) override;
  void closeSession() override;

  // ========== INTERNAL METHODS ==========
  // (In most use cases you won't need these)
  void setup() override;
  void dump_config() override;
  void loop() override;

  uint16_t get_port() const;

 protected:
  void handle_();

  uint16_t port_;

  std::unique_ptr<socket::Socket> server_;
  std::unique_ptr<socket::Socket> client_;
};

}  // namespace ota_socket
}  // namespace esphome
