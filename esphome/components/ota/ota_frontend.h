#pragma once

namespace esphome {
namespace ota {

class OTAFrontend {
 public:
  virtual ~OTAFrontend() = default;
  virtual ssize_t read(uint8_t *buf, size_t len);
  virtual ssize_t write(const uint8_t *buf, size_t len);
  virtual void close_session();
};

}  // namespace ota
}  // namespace esphome
